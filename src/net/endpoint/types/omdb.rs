//! Defines OMDb wire response models.

#![expect(
    missing_docs,
    reason = "fields mirror the external OMDb response schema"
)]

use serde::{Deserialize, Serialize};

/// Title details returned by the OMDb title/ID endpoint.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "PascalCase")]
pub struct TitleResult {
    pub title: String,
    pub year: String,
    pub rated: Option<String>,
    pub released: Option<String>,
    pub runtime: Option<String>,
    pub genre: Option<String>,
    pub director: Option<String>,
    pub writer: Option<String>,
    pub actors: Option<String>,
    pub plot: Option<String>,
    pub language: Option<String>,
    pub country: Option<String>,
    pub awards: Option<String>,
    pub poster: Option<String>,
    pub ratings: Option<Vec<Rating>>,
    pub metascore: Option<String>,
    #[serde(rename = "imdbRating")]
    pub imdb_rating: Option<String>,
    #[serde(rename = "imdbVotes")]
    pub imdb_votes: Option<String>,
    #[serde(rename = "imdbID")]
    pub imdb_id: Option<String>,
    #[serde(rename = "Type")]
    pub media_type: Option<String>,
    pub response: String,
}

/// A single rating entry from an external source.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "PascalCase")]
pub struct Rating {
    pub source: String,
    pub value: String,
}

/// Paginated search results from the OMDb search endpoint.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "PascalCase")]
pub struct SearchResponse {
    pub search: Option<Vec<SearchItem>>,
    #[serde(rename = "totalResults")]
    pub total_results: Option<String>,
    pub response: String,
}

/// A single item in an OMDb search result list.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "PascalCase")]
pub struct SearchItem {
    pub title: String,
    pub year: String,
    #[serde(rename = "imdbID")]
    pub imdb_id: String,
    #[serde(rename = "Type")]
    pub media_type: String,
    pub poster: Option<String>,
}

/// Raw OMDb error response (used internally for parsing error bodies).
#[derive(Debug, Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct ErrorResponse {
    pub response: String,
    pub error: Option<String>,
}
