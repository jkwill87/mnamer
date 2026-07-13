//! Defines TMDb wire response models.

#![expect(
    missing_docs,
    reason = "fields mirror the external TMDb response schema"
)]

use serde::{Deserialize, Serialize};

/// Results from the TMDb find-by-external-ID endpoint.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct FindResponse {
    pub movie_results: Vec<MovieSummary>,
    #[serde(default)]
    pub tv_results: Vec<serde_json::Value>,
    #[serde(default)]
    pub tv_episode_results: Vec<serde_json::Value>,
    #[serde(default)]
    pub tv_season_results: Vec<serde_json::Value>,
    #[serde(default)]
    pub person_results: Vec<serde_json::Value>,
}

/// Brief movie information returned in search and find results.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MovieSummary {
    pub id: u64,
    pub title: String,
    pub original_title: Option<String>,
    pub overview: Option<String>,
    pub release_date: Option<String>,
    pub poster_path: Option<String>,
    pub backdrop_path: Option<String>,
    pub adult: Option<bool>,
    pub genre_ids: Option<Vec<u64>>,
    pub original_language: Option<String>,
    pub popularity: Option<f64>,
    pub vote_average: Option<f64>,
    pub vote_count: Option<u64>,
}

/// Full movie details returned by the TMDb movie endpoint.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct MovieDetails {
    pub id: u64,
    pub title: String,
    pub original_title: Option<String>,
    pub overview: Option<String>,
    pub release_date: Option<String>,
    pub imdb_id: Option<String>,
    pub runtime: Option<u32>,
    pub budget: Option<u64>,
    pub revenue: Option<u64>,
    pub genres: Option<Vec<Genre>>,
    pub poster_path: Option<String>,
    pub backdrop_path: Option<String>,
    pub homepage: Option<String>,
    pub status: Option<String>,
    pub tagline: Option<String>,
    pub original_language: Option<String>,
    pub popularity: Option<f64>,
    pub vote_average: Option<f64>,
    pub vote_count: Option<u64>,
}

/// A movie genre.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Genre {
    pub id: u64,
    pub name: String,
}

/// Paginated movie search results from TMDb.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SearchMoviesResponse {
    pub page: u32,
    pub results: Vec<MovieSummary>,
    pub total_pages: u32,
    pub total_results: u32,
}

/// Raw TMDb error response (used internally for parsing error bodies).
#[derive(Debug, Deserialize)]
pub struct ErrorResponse {
    pub status_message: Option<String>,
    pub status_code: Option<u32>,
}
