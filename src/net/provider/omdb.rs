//! Searches OMDb for movie candidates and normalizes responses.

use super::{Candidate, ProviderError, ProviderKind, ProviderRegistry};
use crate::media::{MediaKind, Metadata};
use crate::net::endpoint::types::omdb::TitleResult;
use crate::net::endpoint::{self as endpoints, EndpointError};

/// Checks OMDb availability and credentials.
pub(super) async fn check(registry: &ProviderRegistry) -> Result<(), ProviderError> {
    let client = registry.client().bypass_cache();
    endpoints::omdb::omdb_search(
        &client,
        registry.credential(ProviderKind::Omdb)?,
        "Fight Club",
        Some(1999),
        Some("movie"),
        Some(1),
    )
    .await?;
    Ok(())
}

/// Searches OMDb for movie candidates.
pub(super) async fn search(
    registry: &ProviderRegistry,
    query: &Metadata,
    max_results: usize,
) -> Result<Vec<Candidate>, ProviderError> {
    let client = registry.client();
    let key = registry.credential(ProviderKind::Omdb)?;
    if let Some(id) = &query.id_imdb {
        let details = endpoints::omdb::omdb_title(
            client,
            key,
            Some(id),
            None,
            None,
            None,
            None,
            Some("full"),
        )
        .await?;
        return Ok(vec![candidate_from_details(details, query)]);
    }
    let title = query
        .name
        .as_deref()
        .ok_or(ProviderError::InvalidQuery(ProviderKind::Omdb))?;
    let mut candidates = Vec::new();
    for page in 1..=5 {
        let response = match endpoints::omdb::omdb_search(
            client,
            key,
            title,
            query.year,
            Some("movie"),
            Some(page),
        )
        .await
        {
            Ok(response) => response,
            Err(EndpointError::NotFound { .. }) => break,
            Err(error) => return Err(error.into()),
        };
        let Some(results) = response.search else {
            break;
        };
        for result in results {
            if !year_matches(query.year, &result.year) {
                continue;
            }
            let details = match endpoints::omdb::omdb_title(
                client,
                key,
                Some(&result.imdb_id),
                None,
                None,
                None,
                None,
                Some("full"),
            )
            .await
            {
                Ok(details) => details,
                Err(EndpointError::NotFound { .. }) => continue,
                Err(error) => return Err(error.into()),
            };
            candidates.push(candidate_from_details(details, query));
            if candidates.len() >= max_results {
                return Ok(candidates);
            }
        }
        let total = response
            .total_results
            .as_deref()
            .and_then(|value| value.parse::<usize>().ok())
            .unwrap_or_default();
        if page as usize * 10 >= total {
            break;
        }
    }
    Ok(candidates)
}

/// Returns whether an OMDb result matches the requested year.
fn year_matches(requested: Option<u16>, result: &str) -> bool {
    requested.is_none_or(|requested| {
        parse_year(result).is_some_and(|result| requested.abs_diff(result) <= 5)
    })
}

/// Normalizes OMDb title details into a candidate.
fn candidate_from_details(details: TitleResult, query: &Metadata) -> Candidate {
    Candidate {
        provider: ProviderKind::Omdb,
        score: details
            .imdb_rating
            .as_deref()
            .and_then(|rating| rating.parse().ok()),
        metadata: Metadata {
            media_type: MediaKind::Movie,
            name: Some(details.title),
            year: parse_year(&details.year),
            synopsis: details.plot.filter(|plot| plot != "N/A"),
            language: query.language.clone(),
            id_imdb: details.imdb_id,
            ..Metadata::default()
        },
    }
}

/// Parses the leading year from an OMDb value.
fn parse_year(value: &str) -> Option<u16> {
    value
        .get(..4)
        .filter(|year| year.chars().all(|character| character.is_ascii_digit()))
        .and_then(|year| year.parse().ok())
}

crate::unit_tests!("omdb.test.rs");
