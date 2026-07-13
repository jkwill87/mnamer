//! Defines TVDb v3 wire response models.

#![expect(
    missing_docs,
    reason = "fields mirror the external TVDb response schema"
)]

use serde::{Deserialize, Serialize};

/// A generic data wrapper with optional pagination links.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct DataResponse<T> {
    pub data: T,
    #[serde(default)]
    pub links: Option<PaginationLinks>,
}

/// Pagination links for paginated API responses.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct PaginationLinks {
    pub first: Option<u32>,
    pub last: Option<u32>,
    pub next: Option<u32>,
    pub prev: Option<u32>,
}

/// A television episode from the TVDb API.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Episode {
    pub id: u64,
    pub aired_episode_number: Option<u32>,
    pub aired_season: Option<u32>,
    pub aired_season_id: Option<u64>,
    pub episode_name: Option<String>,
    pub first_aired: Option<String>,
    pub overview: Option<String>,
    pub series_id: Option<u64>,
    #[serde(rename = "imdbId")]
    pub imdb_id: Option<String>,
    pub absolute_number: Option<u32>,
    pub dvd_episode_number: Option<f64>,
    pub dvd_season: Option<u32>,
    pub directors: Option<Vec<String>>,
    pub writers: Option<Vec<String>>,
    pub guest_stars: Option<Vec<String>>,
    pub content_rating: Option<String>,
    pub filename: Option<String>,
    pub last_updated: Option<u64>,
    pub is_movie: Option<u32>,
}

/// A television series from the TVDb API.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Series {
    pub id: u64,
    pub series_name: Option<String>,
    pub overview: Option<String>,
    pub first_aired: Option<String>,
    pub status: Option<String>,
    pub network: Option<String>,
    pub genre: Option<Vec<String>>,
    pub runtime: Option<String>,
    #[serde(rename = "imdbId")]
    pub imdb_id: Option<String>,
    pub banner: Option<String>,
    pub aliases: Option<Vec<String>>,
    pub series_id: Option<String>,
    pub slug: Option<String>,
    pub added: Option<String>,
    pub site_rating: Option<f64>,
    pub site_rating_count: Option<u32>,
}

/// Raw TVDb login response.
#[derive(Debug, Deserialize)]
pub struct LoginResponse {
    pub token: String,
}

/// Raw TVDb error response (used internally for parsing error bodies).
#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct ErrorResponse {
    pub error: Option<String>,
}
