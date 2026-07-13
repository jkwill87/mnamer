//! Requests and decodes OMDb metadata.

use super::client::{ApiClient, ApiResponse, SemanticCacheKey};
use super::error::EndpointError;
use super::types::omdb::{ErrorResponse, SearchResponse, TitleResult};

/// Defines the provider API base URL.
const BASE_URL: &str = "https://www.omdbapi.com";

/// Parses an OMDb response body.
fn parse_omdb_body<T: serde::de::DeserializeOwned>(body: &str) -> Result<T, EndpointError> {
    let probe: ErrorResponse = serde_json::from_str(body)?;
    if probe.response == "False" {
        let msg = probe.error.unwrap_or_else(|| "unknown error".into());
        if msg.contains("not found") || msg.contains("Incorrect IMDb") {
            return Err(EndpointError::NotFound { message: msg });
        }
        return Err(EndpointError::InvalidRequest {
            message: msg,
            status: 200,
        });
    }
    Ok(serde_json::from_str(body)?)
}

/// Returns whether an OMDb body represents success.
fn is_successful_omdb_json(body: &[u8]) -> bool {
    serde_json::from_slice::<ErrorResponse>(body).is_ok_and(|response| response.response != "False")
}

/// Parses and validates an OMDb HTTP response.
fn parse_response<T: serde::de::DeserializeOwned>(
    response: &ApiResponse,
) -> Result<T, EndpointError> {
    if !response.status.is_success() {
        return Err(EndpointError::InvalidRequest {
            message: format!("HTTP {}", response.status.as_u16()),
            status: response.status.as_u16(),
        });
    }
    parse_omdb_body(&response.text())
}

/// Fetch movie/episode details by IMDb ID or title.
#[expect(
    clippy::too_many_arguments,
    reason = "arguments map directly to optional OMDb query parameters"
)]
pub async fn omdb_title(
    client: &ApiClient,
    api_key: &str,
    id_imdb: Option<&str>,
    title: Option<&str>,
    season: Option<u32>,
    episode: Option<u32>,
    year: Option<u16>,
    plot: Option<&str>,
) -> Result<TitleResult, EndpointError> {
    let mut parameters = vec![("apikey", api_key.to_owned())];
    if let Some(id) = id_imdb {
        parameters.push(("i", id.to_owned()));
    }
    if let Some(title) = title {
        parameters.push(("t", title.to_owned()));
    }
    if let Some(season) = season {
        parameters.push(("Season", season.to_string()));
    }
    if let Some(episode) = episode {
        parameters.push(("Episode", episode.to_string()));
    }
    if let Some(year) = year {
        parameters.push(("y", year.to_string()));
    }
    if let Some(plot) = plot {
        parameters.push(("plot", plot.to_owned()));
    }
    let key = SemanticCacheKey::new("omdb", "title")
        .optional("imdb_id", id_imdb)
        .optional("title", title)
        .optional("season", season)
        .optional("episode", episode)
        .optional("year", year)
        .optional("plot", plot);
    let response = client
        .send_get_validated(
            client.get(BASE_URL).query(&parameters),
            &key,
            is_successful_omdb_json,
        )
        .await?;
    parse_response(&response)
}

/// Search for movies/series by query string.
pub async fn omdb_search(
    client: &ApiClient,
    api_key: &str,
    query: &str,
    year: Option<u16>,
    media: Option<&str>,
    page: Option<u32>,
) -> Result<SearchResponse, EndpointError> {
    let mut parameters = vec![("apikey", api_key.to_owned()), ("s", query.to_owned())];
    if let Some(year) = year {
        parameters.push(("y", year.to_string()));
    }
    if let Some(media) = media {
        parameters.push(("type", media.to_owned()));
    }
    if let Some(page) = page {
        parameters.push(("page", page.to_string()));
    }
    let key = SemanticCacheKey::new("omdb", "search")
        .parameter("query", query)
        .optional("year", year)
        .optional("media", media)
        .optional("page", page);
    let response = client
        .send_get_validated(
            client.get(BASE_URL).query(&parameters),
            &key,
            is_successful_omdb_json,
        )
        .await?;
    parse_response(&response)
}
