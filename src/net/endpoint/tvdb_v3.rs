//! Requests and decodes TVDb v3 metadata.

use mediakit::meta::fields::Language;
use reqwest_middleware::RequestBuilder;

use super::client::{ApiClient, ApiResponse, SemanticCacheKey};
use super::error::EndpointError;
use super::types::tvdb_v3::{DataResponse, Episode, ErrorResponse, LoginResponse, Series};

/// Defines the provider API base URL.
const BASE_URL: &str = "https://api.thetvdb.com";

/// Converts a TVDb error response into an endpoint error.
fn handle_tvdb_error(status: u16, body: &str) -> EndpointError {
    if let Ok(err) = serde_json::from_str::<ErrorResponse>(body)
        && let Some(msg) = err.error
    {
        if status == 404 {
            return EndpointError::NotFound { message: msg };
        }
        return EndpointError::InvalidRequest {
            message: msg,
            status,
        };
    }
    if status == 404 {
        return EndpointError::NotFound {
            message: "resource not found".into(),
        };
    }
    EndpointError::InvalidRequest {
        message: format!("HTTP {status}"),
        status,
    }
}

/// Builds an authenticated TVDb GET request.
fn authenticated_get(
    client: &ApiClient,
    url: &str,
    token: &str,
    language: Option<Language>,
) -> RequestBuilder {
    let mut request = client
        .get(url)
        .header("Authorization", format!("Bearer {token}"));
    if let Some(language) = language {
        request = request.header("Accept-Language", language.iso_639_1);
    }
    request
}

/// Parses and validates a TVDb HTTP response.
fn parse_response<T: serde::de::DeserializeOwned>(
    response: &ApiResponse,
) -> Result<T, EndpointError> {
    if response.status.is_success() {
        response.json()
    } else {
        Err(handle_tvdb_error(
            response.status.as_u16(),
            &response.text(),
        ))
    }
}

/// Authenticate and obtain a JWT token.
pub async fn tvdb_login(client: &ApiClient, api_key: &str) -> Result<String, EndpointError> {
    let response = client
        .send_uncached(
            client
                .post(format!("{BASE_URL}/login"))
                .json(&serde_json::json!({"apikey": api_key})),
        )
        .await?;
    let login: LoginResponse = parse_response(&response)?;
    Ok(login.token)
}

/// Refresh an existing JWT token.
pub async fn tvdb_refresh_token(client: &ApiClient, token: &str) -> Result<String, EndpointError> {
    let response = client
        .send_uncached(
            client
                .get(format!("{BASE_URL}/refresh_token"))
                .header("Authorization", format!("Bearer {token}")),
        )
        .await?;
    let login: LoginResponse = parse_response(&response)?;
    Ok(login.token)
}

/// Get episode details by TVDb episode ID.
pub async fn tvdb_episodes_id(
    client: &ApiClient,
    token: &str,
    id_tvdb: u64,
    language: Option<Language>,
) -> Result<DataResponse<Episode>, EndpointError> {
    let url = format!("{BASE_URL}/episodes/{id_tvdb}");
    let key = SemanticCacheKey::new("tvdb-v3", "episode")
        .parameter("id", id_tvdb)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client
        .send_get(authenticated_get(client, &url, token, language), &key)
        .await?;
    parse_response(&response)
}

/// Get series details by TVDb series ID.
pub async fn tvdb_series_id(
    client: &ApiClient,
    token: &str,
    id_tvdb: u64,
    language: Option<Language>,
) -> Result<DataResponse<Series>, EndpointError> {
    let url = format!("{BASE_URL}/series/{id_tvdb}");
    let key = SemanticCacheKey::new("tvdb-v3", "series")
        .parameter("id", id_tvdb)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client
        .send_get(authenticated_get(client, &url, token, language), &key)
        .await?;
    parse_response(&response)
}

/// Get paginated episode list for a series.
pub async fn tvdb_series_id_episodes(
    client: &ApiClient,
    token: &str,
    id_tvdb: u64,
    page: Option<u32>,
    language: Option<Language>,
) -> Result<DataResponse<Vec<Episode>>, EndpointError> {
    let url = format!("{BASE_URL}/series/{id_tvdb}/episodes");
    let mut request = authenticated_get(client, &url, token, language);
    if let Some(page) = page {
        request = request.query(&[("page", page)]);
    }
    let key = SemanticCacheKey::new("tvdb-v3", "series-episodes")
        .parameter("id", id_tvdb)
        .optional("page", page)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client.send_get(request, &key).await?;
    parse_response(&response)
}

/// Query episodes for a series with optional season/episode filters.
pub async fn tvdb_series_id_episodes_query(
    client: &ApiClient,
    token: &str,
    id_tvdb: u64,
    episode: Option<u32>,
    season: Option<u32>,
    page: Option<u32>,
    language: Option<Language>,
) -> Result<DataResponse<Vec<Episode>>, EndpointError> {
    let url = format!("{BASE_URL}/series/{id_tvdb}/episodes/query");
    let mut parameters = Vec::new();
    if let Some(episode) = episode {
        parameters.push(("airedEpisode", episode));
    }
    if let Some(season) = season {
        parameters.push(("airedSeason", season));
    }
    if let Some(page) = page {
        parameters.push(("page", page));
    }
    let request = authenticated_get(client, &url, token, language).query(&parameters);
    let key = SemanticCacheKey::new("tvdb-v3", "series-episodes-query")
        .parameter("id", id_tvdb)
        .optional("episode", episode)
        .optional("season", season)
        .optional("page", page)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client.send_get(request, &key).await?;
    parse_response(&response)
}

/// Search for series by name or external ID.
pub async fn tvdb_search_series(
    client: &ApiClient,
    token: &str,
    series: Option<&str>,
    id_imdb: Option<&str>,
    id_zap2it: Option<&str>,
    language: Option<Language>,
) -> Result<DataResponse<Vec<Series>>, EndpointError> {
    let url = format!("{BASE_URL}/search/series");
    let mut parameters = Vec::new();
    if let Some(series) = series {
        parameters.push(("name", series.to_owned()));
    }
    if let Some(id_imdb) = id_imdb {
        parameters.push(("imdbId", id_imdb.to_owned()));
    }
    if let Some(id_zap2it) = id_zap2it {
        parameters.push(("zap2itId", id_zap2it.to_owned()));
    }
    let request = authenticated_get(client, &url, token, language).query(&parameters);
    let key = SemanticCacheKey::new("tvdb-v3", "search-series")
        .optional("series", series)
        .optional("imdb_id", id_imdb)
        .optional("zap2it_id", id_zap2it)
        .optional("language", language.map(|value| value.iso_639_1));
    let response = client.send_get(request, &key).await?;
    parse_response(&response)
}
