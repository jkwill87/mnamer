//! Defines TVmaze wire response models.

#![expect(
    missing_docs,
    reason = "fields mirror the external TVmaze response schema"
)]

use serde::{Deserialize, Serialize};

/// A television show from the TVmaze API.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Show {
    pub id: u64,
    pub name: String,
    #[serde(rename = "type")]
    pub show_type: Option<String>,
    pub language: Option<String>,
    #[serde(default)]
    pub genres: Vec<String>,
    pub status: Option<String>,
    pub runtime: Option<u32>,
    pub premiered: Option<String>,
    pub ended: Option<String>,
    #[serde(rename = "officialSite")]
    pub official_site: Option<String>,
    pub schedule: Option<Schedule>,
    pub rating: Option<ShowRating>,
    pub weight: Option<u32>,
    pub network: Option<Network>,
    #[serde(rename = "webChannel")]
    pub web_channel: Option<serde_json::Value>,
    pub externals: Option<Externals>,
    pub image: Option<Image>,
    pub summary: Option<String>,
    pub updated: Option<u64>,
    #[serde(rename = "_embedded")]
    pub embedded: Option<Embedded>,
}

/// A show's broadcast schedule.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Schedule {
    pub time: Option<String>,
    #[serde(default)]
    pub days: Vec<String>,
}

/// A show's average user rating.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct ShowRating {
    pub average: Option<f64>,
}

/// A television network.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Network {
    pub id: u64,
    pub name: String,
    pub country: Option<Country>,
}

/// A country with timezone information.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Country {
    pub name: String,
    pub code: String,
    pub timezone: Option<String>,
}

/// External IDs linking to other databases.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Externals {
    pub tvrage: Option<u64>,
    pub thetvdb: Option<u64>,
    pub imdb: Option<String>,
}

/// Image URLs in medium and original sizes.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Image {
    pub medium: Option<String>,
    pub original: Option<String>,
}

/// Embedded resources included via `?embed=` query parameters.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Embedded {
    #[serde(default)]
    pub episodes: Vec<Episode>,
}

/// A television episode from the TVmaze API.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Episode {
    pub id: u64,
    pub name: Option<String>,
    pub season: Option<u32>,
    pub number: Option<u32>,
    #[serde(rename = "type")]
    pub episode_type: Option<String>,
    pub airdate: Option<String>,
    pub airtime: Option<String>,
    pub airstamp: Option<String>,
    pub runtime: Option<u32>,
    pub summary: Option<String>,
    pub image: Option<Image>,
    pub rating: Option<ShowRating>,
}

/// A ranked search result containing a show and its relevance score.
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct SearchResult {
    pub score: f64,
    pub show: Show,
}
