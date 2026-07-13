//! Requests and decodes TVmaze metadata.

use super::client::{ApiClient, ApiResponse, SemanticCacheKey};
use super::error::EndpointError;
use super::types::tvmaze::{Episode, SearchResult, Show};

/// Defines the provider API base URL.
const BASE_URL: &str = "https://api.tvmaze.com";

/// Parses and validates a TVmaze HTTP response.
fn parse_response<T: serde::de::DeserializeOwned>(
    response: &ApiResponse,
) -> Result<T, EndpointError> {
    if response.status.is_success() {
        response.json()
    } else {
        Err(EndpointError::InvalidRequest {
            message: format!("HTTP {}", response.status.as_u16()),
            status: response.status.as_u16(),
        })
    }
}

/// Get show details by TVmaze ID, optionally embedding episodes.
pub async fn tvmaze_show(
    client: &ApiClient,
    id_tvmaze: u64,
    embed_episodes: bool,
) -> Result<Show, EndpointError> {
    let url = format!("{BASE_URL}/shows/{id_tvmaze}");
    let mut request = client.get(url);
    if embed_episodes {
        request = request.query(&[("embed", "episodes")]);
    }
    let key = SemanticCacheKey::new("tvmaze", "show")
        .parameter("id", id_tvmaze)
        .parameter("embed_episodes", embed_episodes);
    let response = client.send_get(request, &key).await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: format!("TVmaze show {id_tvmaze} not found"),
        });
    }
    parse_response(&response)
}

/// Search for shows by query string (returns ranked list).
pub async fn tvmaze_show_search(
    client: &ApiClient,
    query: &str,
) -> Result<Vec<SearchResult>, EndpointError> {
    let key = SemanticCacheKey::new("tvmaze", "show-search").parameter("query", query);
    let response = client
        .send_get(
            client
                .get(format!("{BASE_URL}/search/shows"))
                .query(&[("q", query)]),
            &key,
        )
        .await?;
    parse_response(&response)
}

/// Search for a single show by query (returns best match).
pub async fn tvmaze_show_single_search(
    client: &ApiClient,
    query: &str,
) -> Result<Show, EndpointError> {
    let key = SemanticCacheKey::new("tvmaze", "show-single-search").parameter("query", query);
    let response = client
        .send_get(
            client
                .get(format!("{BASE_URL}/singlesearch/shows"))
                .query(&[("q", query)]),
            &key,
        )
        .await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: format!("no show found for query \"{query}\""),
        });
    }
    parse_response(&response)
}

/// Look up a show by external ID (IMDb or TVDb).
pub async fn tvmaze_show_lookup(
    client: &ApiClient,
    id_imdb: Option<&str>,
    id_tvdb: Option<u64>,
) -> Result<Show, EndpointError> {
    if id_imdb.is_some() == id_tvdb.is_some() {
        return Err(EndpointError::InvalidRequest {
            message: "exactly one IMDb or TVDb ID is required".into(),
            status: 0,
        });
    }
    let mut parameters = Vec::new();
    if let Some(id_imdb) = id_imdb {
        parameters.push(("imdb", id_imdb.to_owned()));
    }
    if let Some(id_tvdb) = id_tvdb {
        parameters.push(("thetvdb", id_tvdb.to_string()));
    }
    let key = SemanticCacheKey::new("tvmaze", "show-lookup")
        .optional("imdb_id", id_imdb)
        .optional("tvdb_id", id_tvdb);
    let response = client
        .send_get(
            client
                .get(format!("{BASE_URL}/lookup/shows"))
                .query(&parameters),
            &key,
        )
        .await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: "no show found for given external ID".into(),
        });
    }
    if !response.status.is_success() {
        return Err(EndpointError::InvalidRequest {
            message: format!("HTTP {}", response.status.as_u16()),
            status: response.status.as_u16(),
        });
    }
    response.json()
}

/// Get all episodes for a show.
pub async fn tvmaze_show_episodes_list(
    client: &ApiClient,
    id_tvmaze: u64,
    include_specials: bool,
) -> Result<Vec<Episode>, EndpointError> {
    let mut request = client.get(format!("{BASE_URL}/shows/{id_tvmaze}/episodes"));
    if include_specials {
        request = request.query(&[("specials", "1")]);
    }
    let key = SemanticCacheKey::new("tvmaze", "show-episodes")
        .parameter("id", id_tvmaze)
        .parameter("include_specials", include_specials);
    let response = client.send_get(request, &key).await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: format!("TVmaze show {id_tvmaze} not found"),
        });
    }
    parse_response(&response)
}

/// Get episodes that aired on a specific date.
pub async fn tvmaze_episodes_by_date(
    client: &ApiClient,
    id_tvmaze: u64,
    air_date: &str,
) -> Result<Vec<Episode>, EndpointError> {
    let key = SemanticCacheKey::new("tvmaze", "episodes-by-date")
        .parameter("id", id_tvmaze)
        .parameter("air_date", air_date);
    let response = client
        .send_get(
            client
                .get(format!("{BASE_URL}/shows/{id_tvmaze}/episodesbydate"))
                .query(&[("date", air_date)]),
            &key,
        )
        .await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: format!("no episodes found for show {id_tvmaze} on {air_date}"),
        });
    }
    parse_response(&response)
}

/// Get a single episode by season and episode number.
pub async fn tvmaze_episode_by_number(
    client: &ApiClient,
    id_tvmaze: u64,
    season: u32,
    episode: u32,
) -> Result<Episode, EndpointError> {
    let key = SemanticCacheKey::new("tvmaze", "episode-by-number")
        .parameter("id", id_tvmaze)
        .parameter("season", season)
        .parameter("episode", episode);
    let response = client
        .send_get(
            client
                .get(format!("{BASE_URL}/shows/{id_tvmaze}/episodebynumber"))
                .query(&[("season", season), ("number", episode)]),
            &key,
        )
        .await?;
    if response.status.as_u16() == 404 {
        return Err(EndpointError::NotFound {
            message: format!("episode S{season:02}E{episode:02} not found for show {id_tvmaze}"),
        });
    }
    parse_response(&response)
}
