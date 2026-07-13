//! Searches TVDb for episode candidates and normalizes responses.

use super::{Candidate, ProviderError, ProviderKind, ProviderRegistry};
use crate::media::{MediaKind, Metadata};
use crate::net::endpoint::types::tvdb_v3::{Episode, Series};
use crate::net::endpoint::{self as endpoints, EndpointError};
use mediakit::meta::fields::Language;

/// Checks TVDb availability and credentials.
pub(super) async fn check(registry: &ProviderRegistry) -> Result<(), ProviderError> {
    let client = registry.client().bypass_cache();
    endpoints::tvdb_v3::tvdb_login(&client, registry.credential(ProviderKind::Tvdb)?).await?;
    Ok(())
}

/// Searches TVDb for episode candidates.
pub(super) async fn search(
    registry: &ProviderRegistry,
    query: &Metadata,
    max_results: usize,
) -> Result<Vec<Candidate>, ProviderError> {
    let client = registry.client();
    let token = registry.tvdb_token().await?;
    let language = provider_language(query);
    if let Some(language) = language
        && !supports_language(language)
    {
        return Err(ProviderError::UnsupportedLanguage {
            provider: ProviderKind::Tvdb,
            language: language.iso_639_1.into(),
        });
    }
    let series_ids = if let Some(id) = &query.id_tvdb {
        vec![parse_id(id)?]
    } else if let Some(id_imdb) = &query.id_imdb {
        endpoints::tvdb_v3::tvdb_search_series(client, &token, None, Some(id_imdb), None, language)
            .await?
            .data
            .into_iter()
            .take(5)
            .map(|series| series.id)
            .collect()
    } else {
        let series = query
            .series
            .as_deref()
            .ok_or(ProviderError::InvalidQuery(ProviderKind::Tvdb))?;
        endpoints::tvdb_v3::tvdb_search_series(client, &token, Some(series), None, None, language)
            .await?
            .data
            .into_iter()
            .take(5)
            .map(|series| series.id)
            .collect()
    };

    let mut candidates = Vec::new();
    for series_id in series_ids {
        let series =
            match endpoints::tvdb_v3::tvdb_series_id(client, &token, series_id, language).await {
                Ok(response) => response.data,
                Err(EndpointError::NotFound { .. }) => continue,
                Err(error) => return Err(error.into()),
            };
        let mut page = 1;
        loop {
            let response = match endpoints::tvdb_v3::tvdb_series_id_episodes_query(
                client,
                &token,
                series_id,
                query.episode.map(u32::from),
                query.season.map(u32::from),
                Some(page),
                language,
            )
            .await
            {
                Ok(response) => response,
                Err(EndpointError::NotFound { .. }) => break,
                Err(error) => return Err(error.into()),
            };
            for episode in response.data {
                if query
                    .date
                    .as_ref()
                    .is_some_and(|date| episode.first_aired.as_deref() != Some(date.as_str()))
                {
                    continue;
                }
                candidates.push(candidate_from_episode(
                    &series, episode, series_id, language,
                ));
                if candidates.len() >= max_results {
                    return Ok(candidates);
                }
            }
            let Some(next) = response.links.and_then(|links| links.next) else {
                break;
            };
            if next <= page || page >= 20 {
                break;
            }
            page = next;
        }
    }
    Ok(candidates)
}

/// Resolves the TVDb request language.
fn provider_language(query: &Metadata) -> Option<Language> {
    query
        .language
        .as_deref()
        .and_then(Language::from_identifier)
}

/// Returns whether TVDb v3 supports a language.
fn supports_language(language: Language) -> bool {
    matches!(
        language.iso_639_1,
        "cs" | "da"
            | "de"
            | "el"
            | "en"
            | "es"
            | "fi"
            | "fr"
            | "he"
            | "hr"
            | "hu"
            | "it"
            | "ja"
            | "ko"
            | "nl"
            | "no"
            | "pl"
            | "pt"
            | "ru"
            | "sl"
            | "sv"
            | "tr"
            | "zh"
    )
}

/// Parses a TVDb identifier.
fn parse_id(value: &str) -> Result<u64, ProviderError> {
    value.parse().map_err(|_| ProviderError::InvalidIdentifier {
        provider: ProviderKind::Tvdb,
        value: value.into(),
    })
}

/// Normalizes a TVDb episode into a candidate.
fn candidate_from_episode(
    series: &Series,
    episode: Episode,
    series_id: u64,
    language: Option<Language>,
) -> Candidate {
    Candidate {
        provider: ProviderKind::Tvdb,
        score: series.site_rating,
        metadata: Metadata {
            media_type: MediaKind::Episode,
            series: series.series_name.clone(),
            title: episode
                .episode_name
                .and_then(|title| title.split(';').next().map(str::trim).map(str::to_owned)),
            season: episode.aired_season.and_then(u32_to_u16),
            episode: episode.aired_episode_number.and_then(u32_to_u16),
            date: episode.first_aired,
            synopsis: episode.overview.map(|value| value.replace("\r\n", " ")),
            language: language.map(|language| language.iso_639_1.into()),
            id_imdb: episode.imdb_id.or_else(|| series.imdb_id.clone()),
            id_tvdb: Some(series_id.to_string()),
            ..Metadata::default()
        },
    }
}

/// Converts a provider integer into a metadata integer.
fn u32_to_u16(value: u32) -> Option<u16> {
    u16::try_from(value).ok()
}

crate::unit_tests!("tvdb.test.rs");
