//! Searches TMDb for movie candidates and normalizes responses.

use super::{Candidate, ProviderError, ProviderKind, ProviderRegistry};
use crate::media::{MediaKind, Metadata};
use crate::net::endpoint::types::tmdb::{MovieDetails, MovieSummary};
use crate::net::endpoint::{self as endpoints};
use mediakit::meta::fields::Language;

/// Checks TMDb availability and credentials.
pub(super) async fn check(registry: &ProviderRegistry) -> Result<(), ProviderError> {
    let client = registry.client().bypass_cache();
    endpoints::tmdb::tmdb_search_movies(
        &client,
        registry.credential(ProviderKind::Tmdb)?,
        "Fight Club",
        Some(1999),
        None,
        None,
        Some(false),
        Some(1),
    )
    .await?;
    Ok(())
}

/// Searches TMDb for movie candidates.
pub(super) async fn search(
    registry: &ProviderRegistry,
    query: &Metadata,
    max_results: usize,
) -> Result<Vec<Candidate>, ProviderError> {
    let client = registry.client();
    let key = registry.credential(ProviderKind::Tmdb)?;
    let language = provider_language(query);
    if let Some(id) = &query.id_tmdb {
        let id = parse_id(id)?;
        let details = endpoints::tmdb::tmdb_movies(client, key, id, language).await?;
        return Ok(vec![candidate_from_details(details, language)]);
    }
    if let Some(id_imdb) = &query.id_imdb {
        let response =
            endpoints::tmdb::tmdb_find(client, key, id_imdb, "imdb_id", language).await?;
        return Ok(response
            .movie_results
            .into_iter()
            .take(max_results)
            .enumerate()
            .map(|(index, movie)| candidate_from_summary(movie, language, index))
            .collect());
    }
    let title = query
        .name
        .as_deref()
        .ok_or(ProviderError::InvalidQuery(ProviderKind::Tmdb))?;
    let mut candidates = Vec::new();
    for page in 1..=5 {
        let response = endpoints::tmdb::tmdb_search_movies(
            client,
            key,
            title,
            None,
            language,
            None,
            Some(false),
            Some(page),
        )
        .await?;
        for movie in response.results {
            let index = candidates.len();
            candidates.push(candidate_from_summary(movie, language, index));
            if candidates.len() >= max_results {
                return Ok(candidates);
            }
        }
        if page >= response.total_pages {
            break;
        }
    }
    Ok(candidates)
}

/// Resolves the TMDb request language.
fn provider_language(query: &Metadata) -> Option<Language> {
    query
        .language
        .as_deref()
        .and_then(Language::from_identifier)
}

/// Parses a TMDb identifier.
fn parse_id(value: &str) -> Result<u64, ProviderError> {
    value.parse().map_err(|_| ProviderError::InvalidIdentifier {
        provider: ProviderKind::Tmdb,
        value: value.into(),
    })
}

/// Normalizes TMDb movie details into a candidate.
fn candidate_from_details(details: MovieDetails, language: Option<Language>) -> Candidate {
    Candidate {
        provider: ProviderKind::Tmdb,
        score: details.popularity,
        metadata: Metadata {
            media_type: MediaKind::Movie,
            name: Some(details.title),
            year: details.release_date.as_deref().and_then(parse_year),
            synopsis: details.overview,
            language: language.map(|language| language.iso_639_1.into()),
            id_imdb: details.imdb_id,
            id_tmdb: Some(details.id.to_string()),
            ..Metadata::default()
        },
    }
}

/// Normalizes a TMDb movie summary into a candidate.
fn candidate_from_summary(
    movie: MovieSummary,
    language: Option<Language>,
    index: usize,
) -> Candidate {
    Candidate {
        provider: ProviderKind::Tmdb,
        score: movie
            .popularity
            .or_else(|| Some(1.0 / (index.saturating_add(1) as f64))),
        metadata: Metadata {
            media_type: MediaKind::Movie,
            name: Some(movie.title),
            year: movie.release_date.as_deref().and_then(parse_year),
            synopsis: movie.overview,
            language: language.map(|language| language.iso_639_1.into()),
            id_tmdb: Some(movie.id.to_string()),
            ..Metadata::default()
        },
    }
}

/// Parses a release year.
fn parse_year(value: &str) -> Option<u16> {
    value
        .get(..4)
        .filter(|year| year.chars().all(|character| character.is_ascii_digit()))
        .and_then(|year| year.parse().ok())
}

crate::unit_tests!("tmdb.test.rs");
