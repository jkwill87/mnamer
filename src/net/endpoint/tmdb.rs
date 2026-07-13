//! Requests and decodes TMDb metadata.

use mediakit::meta::fields::Language;

use super::client::{ApiClient, ApiResponse, SemanticCacheKey};
use super::error::EndpointError;
use super::types::tmdb::{ErrorResponse, FindResponse, MovieDetails, SearchMoviesResponse};

/// Defines the provider API base URL.
const BASE_URL: &str = "https://api.themoviedb.org/3";

/// Converts a TMDb error response into an endpoint error.
fn handle_tmdb_error(status: u16, body: &str) -> EndpointError {
    if let Ok(err) = serde_json::from_str::<ErrorResponse>(body) {
        let msg = err.status_message.unwrap_or_else(|| "unknown error".into());
        if status == 404 {
            return EndpointError::NotFound { message: msg };
        }
        return EndpointError::InvalidRequest {
            message: msg,
            status,
        };
    }
    EndpointError::InvalidRequest {
        message: format!("HTTP {status}"),
        status,
    }
}

/// Parses and validates a TMDb HTTP response.
fn parse_response<T: serde::de::DeserializeOwned>(
    response: &ApiResponse,
) -> Result<T, EndpointError> {
    if response.status.is_success() {
        response.json()
    } else {
        Err(handle_tmdb_error(
            response.status.as_u16(),
            &response.text(),
        ))
    }
}

/// Find media by external ID (e.g., IMDb ID).
pub async fn tmdb_find(
    client: &ApiClient,
    api_key: &str,
    external_id: &str,
    external_source: &str,
    language: Option<Language>,
) -> Result<FindResponse, EndpointError> {
    let url = format!("{BASE_URL}/find/{external_id}");
    let mut parameters = vec![
        ("api_key", api_key.to_owned()),
        ("external_source", external_source.to_owned()),
    ];
    if let Some(language) = language {
        parameters.push(("language", language.iso_639_1.to_owned()));
    }
    let key = SemanticCacheKey::new("tmdb", "find")
        .parameter("external_id", external_id)
        .parameter("external_source", external_source)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client
        .send_get(client.get(url).query(&parameters), &key)
        .await?;
    parse_response(&response)
}

/// Get movie details by TMDb ID.
pub async fn tmdb_movies(
    client: &ApiClient,
    api_key: &str,
    id_tmdb: u64,
    language: Option<Language>,
) -> Result<MovieDetails, EndpointError> {
    let url = format!("{BASE_URL}/movie/{id_tmdb}");
    let mut parameters = vec![("api_key", api_key.to_owned())];
    if let Some(language) = language {
        parameters.push(("language", language.iso_639_1.to_owned()));
    }
    let key = SemanticCacheKey::new("tmdb", "movie")
        .parameter("id", id_tmdb)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client
        .send_get(client.get(url).query(&parameters), &key)
        .await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: format!("TMDb movie {id_tmdb} not found"),
        });
    }
    parse_response(&response)
}

/// Search for movies by title.
#[expect(
    clippy::too_many_arguments,
    reason = "arguments map directly to optional TMDb query parameters"
)]
pub async fn tmdb_search_movies(
    client: &ApiClient,
    api_key: &str,
    title: &str,
    year: Option<u16>,
    language: Option<Language>,
    region: Option<&str>,
    adult: Option<bool>,
    page: Option<u32>,
) -> Result<SearchMoviesResponse, EndpointError> {
    let mut parameters = vec![("api_key", api_key.to_owned()), ("query", title.to_owned())];
    if let Some(year) = year {
        parameters.push(("year", year.to_string()));
    }
    if let Some(language) = language {
        parameters.push(("language", language.iso_639_1.to_owned()));
    }
    if let Some(region) = region {
        parameters.push(("region", region.to_owned()));
    }
    if let Some(adult) = adult {
        parameters.push(("include_adult", adult.to_string()));
    }
    if let Some(page) = page {
        parameters.push(("page", page.to_string()));
    }
    let key = SemanticCacheKey::new("tmdb", "search-movies")
        .parameter("title", title)
        .optional("year", year)
        .optional("language", language.map(|value| value.iso_639_1))
        .optional("region", region)
        .optional("adult", adult)
        .optional("page", page);
    let response = client
        .send_get(
            client
                .get(format!("{BASE_URL}/search/movie"))
                .query(&parameters),
            &key,
        )
        .await?;
    parse_response(&response)
}
