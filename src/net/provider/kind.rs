//! Defines supported metadata-provider identities and capabilities.

use crate::media::MediaKind;
use serde::{Deserialize, Serialize};

/// A metadata provider supported by mnamer.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ProviderKind {
    /// The Movie Database.
    Tmdb,
    /// The Open Movie Database.
    Omdb,
    /// TheTVDB v3 API.
    Tvdb,
    /// TVmaze.
    Tvmaze,
}

impl ProviderKind {
    /// All supported providers in stable display order.
    pub const ALL: [Self; 4] = [Self::Tmdb, Self::Omdb, Self::Tvdb, Self::Tvmaze];

    /// Returns the API-key environment variable for an authenticated provider.
    pub const fn api_key_environment_variable(self) -> Option<&'static str> {
        match self {
            Self::Tmdb => Some("API_KEY_TMDB"),
            Self::Omdb => Some("API_KEY_OMDB"),
            Self::Tvdb => Some("API_KEY_TVDB"),
            Self::Tvmaze => None,
        }
    }

    /// Returns whether the current endpoint contract requires authentication.
    pub const fn requires_authentication(self) -> bool {
        !matches!(self, Self::Tvmaze)
    }

    /// Returns whether this provider serves the requested media category.
    pub const fn supports(self, media: MediaKind) -> bool {
        matches!(
            (self, media),
            (Self::Tmdb | Self::Omdb, MediaKind::Movie)
                | (Self::Tvdb | Self::Tvmaze, MediaKind::Episode)
        )
    }
}

impl std::str::FromStr for ProviderKind {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value.to_ascii_lowercase().as_str() {
            "tmdb" => Ok(Self::Tmdb),
            "omdb" => Ok(Self::Omdb),
            "tvdb" => Ok(Self::Tvdb),
            "tvmaze" => Ok(Self::Tvmaze),
            _ => Err(format!("unsupported provider: {value}")),
        }
    }
}

impl std::fmt::Display for ProviderKind {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(match self {
            Self::Tmdb => "tmdb",
            Self::Omdb => "omdb",
            Self::Tvdb => "tvdb",
            Self::Tvmaze => "tvmaze",
        })
    }
}
