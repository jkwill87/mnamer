//! Searches TVmaze for episode candidates and normalizes responses.

use super::{Candidate, ProviderError, ProviderKind, ProviderRegistry};
use crate::media::{MediaKind, Metadata};
use crate::net::endpoint::types::tvmaze::{Episode, Show};
use crate::net::endpoint::{self as endpoints, EndpointError};

/// Checks TVmaze availability.
pub(super) async fn check(registry: &ProviderRegistry) -> Result<(), ProviderError> {
    let client = registry.client().bypass_cache();
    endpoints::tvmaze::tvmaze_show_single_search(&client, "The Expanse").await?;
    Ok(())
}

/// Searches TVmaze for episode candidates.
pub(super) async fn search(
    registry: &ProviderRegistry,
    query: &Metadata,
    max_results: usize,
) -> Result<Vec<Candidate>, ProviderError> {
    let client = registry.client();
    let shows = if let Some(id) = &query.id_tvmaze {
        let id = parse_id(ProviderKind::Tvmaze, id)?;
        vec![(
            None,
            endpoints::tvmaze::tvmaze_show(client, id, false).await?,
        )]
    } else if query.id_tvdb.is_some() || query.id_imdb.is_some() {
        let id_tvdb = query
            .id_tvdb
            .as_deref()
            .map(|id| parse_id(ProviderKind::Tvdb, id))
            .transpose()?;
        let id_imdb = id_tvdb
            .is_none()
            .then_some(query.id_imdb.as_deref())
            .flatten();
        vec![(
            None,
            endpoints::tvmaze::tvmaze_show_lookup(client, id_imdb, id_tvdb).await?,
        )]
    } else {
        let series = query
            .series
            .as_deref()
            .ok_or(ProviderError::InvalidQuery(ProviderKind::Tvmaze))?;
        endpoints::tvmaze::tvmaze_show_search(client, series)
            .await?
            .into_iter()
            .take(5)
            .map(|result| (Some(result.score), result.show))
            .collect()
    };

    let mut candidates = Vec::new();
    for (score, show) in shows {
        let episodes = match episodes_for(client, query, &show).await {
            Ok(episodes) => episodes,
            Err(ProviderError::Endpoint(EndpointError::NotFound { .. })) => continue,
            Err(error) => return Err(error),
        };
        for episode in episodes {
            candidates.push(candidate_from_episode(&show, episode, score));
            if candidates.len() >= max_results {
                return Ok(candidates);
            }
        }
    }
    Ok(candidates)
}

/// Fetches episodes for a TVmaze show.
async fn episodes_for(
    client: &crate::net::endpoint::ApiClient,
    query: &Metadata,
    show: &Show,
) -> Result<Vec<Episode>, ProviderError> {
    if let Some(date) = &query.date {
        return Ok(endpoints::tvmaze::tvmaze_episodes_by_date(client, show.id, date).await?);
    }
    if let (Some(season), Some(episode)) = (query.season, query.episode) {
        return Ok(vec![
            endpoints::tvmaze::tvmaze_episode_by_number(
                client,
                show.id,
                season.into(),
                episode.into(),
            )
            .await?,
        ]);
    }
    let episodes = endpoints::tvmaze::tvmaze_show_episodes_list(client, show.id, true).await?;
    Ok(episodes
        .into_iter()
        .filter(|episode| {
            query
                .season
                .is_none_or(|season| episode.season == Some(season.into()))
                && query
                    .episode
                    .is_none_or(|number| episode.number == Some(number.into()))
        })
        .collect())
}

/// Parses a TVmaze identifier.
fn parse_id(provider: ProviderKind, value: &str) -> Result<u64, ProviderError> {
    value.parse().map_err(|_| ProviderError::InvalidIdentifier {
        provider,
        value: value.into(),
    })
}

/// Normalizes a TVmaze episode into a candidate.
fn candidate_from_episode(show: &Show, episode: Episode, score: Option<f64>) -> Candidate {
    Candidate {
        provider: ProviderKind::Tvmaze,
        score,
        metadata: Metadata {
            media_type: MediaKind::Episode,
            series: Some(show.name.clone()),
            title: episode.name,
            season: episode.season.and_then(u32_to_u16),
            episode: episode.number.and_then(u32_to_u16),
            date: episode.airdate,
            synopsis: episode.summary.map(|summary| strip_html(&summary)),
            id_imdb: show.externals.as_ref().and_then(|ids| ids.imdb.clone()),
            id_tvdb: show
                .externals
                .as_ref()
                .and_then(|ids| ids.thetvdb)
                .map(|id| id.to_string()),
            id_tvmaze: Some(show.id.to_string()),
            ..Metadata::default()
        },
    }
}

/// Converts a provider integer into a metadata integer.
fn u32_to_u16(value: u32) -> Option<u16> {
    u16::try_from(value).ok()
}

/// Removes HTML markup from provider text.
fn strip_html(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut in_tag = false;
    for character in value.chars() {
        match character {
            '<' => in_tag = true,
            '>' => in_tag = false,
            _ if !in_tag => output.push(character),
            _ => {}
        }
    }
    output.trim().to_owned()
}

crate::unit_tests!("tvmaze.test.rs");
