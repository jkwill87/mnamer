//! Defines scalar command-line values and parsers.

use clap::ValueEnum;
use serde::Serialize;
use std::{fmt, str::FromStr};

/// Media classification requested for an invocation.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, ValueEnum)]
#[serde(rename_all = "snake_case")]
pub enum MediaMode {
    /// Detect movie or episode metadata from each filename.
    #[default]
    Auto,
    /// Parse every target as a movie.
    Movie,
    /// Parse every target as an episode.
    Episode,
}

/// Supported namespaces for a typed external ID.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExternalIdSource {
    /// IMDb title identifier.
    Imdb,
    /// TMDb movie identifier.
    Tmdb,
    /// TVDb series or episode identifier.
    Tvdb,
    /// TVmaze show or episode identifier.
    Tvmaze,
}

impl fmt::Display for ExternalIdSource {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(match self {
            Self::Imdb => "imdb",
            Self::Tmdb => "tmdb",
            Self::Tvdb => "tvdb",
            Self::Tvmaze => "tvmaze",
        })
    }
}

impl FromStr for ExternalIdSource {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value.to_ascii_lowercase().as_str() {
            "imdb" => Ok(Self::Imdb),
            "tmdb" => Ok(Self::Tmdb),
            "tvdb" => Ok(Self::Tvdb),
            "tvmaze" => Ok(Self::Tvmaze),
            _ => Err(format!(
                "unsupported ID source {value:?}; expected imdb, tmdb, tvdb, or tvmaze"
            )),
        }
    }
}

/// A provider or external identifier parsed from `SOURCE:ID`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ExternalId {
    /// Identifier namespace.
    pub source: ExternalIdSource,
    /// Identifier value without its namespace prefix.
    pub value: String,
}

impl fmt::Display for ExternalId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}:{}", self.source, self.value)
    }
}

impl FromStr for ExternalId {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let (source, id) = value
            .split_once(':')
            .ok_or_else(|| "external ID must use SOURCE:ID syntax".to_owned())?;
        let source = source.parse()?;
        let id = id.trim();
        if id.is_empty() {
            return Err("external ID value must not be empty".to_owned());
        }
        if id.contains(':') {
            return Err("external ID must contain exactly one ':' separator".to_owned());
        }
        let valid = match source {
            ExternalIdSource::Imdb => id.strip_prefix("tt").is_some_and(|digits| {
                !digits.is_empty() && digits.chars().all(|ch| ch.is_ascii_digit())
            }),
            ExternalIdSource::Tmdb | ExternalIdSource::Tvdb | ExternalIdSource::Tvmaze => {
                id.chars().all(|ch| ch.is_ascii_digit())
                    && id.parse::<u64>().is_ok_and(|value| value > 0)
            }
        };
        if !valid {
            return Err(match source {
                ExternalIdSource::Imdb => {
                    "IMDb IDs must use tt followed by decimal digits".to_owned()
                }
                _ => format!("{source} IDs must be positive decimal integers"),
            });
        }
        Ok(Self {
            source,
            value: id.to_owned(),
        })
    }
}

/// Parses and normalizes a file extension.
pub(super) fn parse_extension(value: &str) -> Result<String, String> {
    let extension = value.trim().trim_start_matches('.').to_ascii_lowercase();
    if extension.is_empty() {
        return Err("extension must not be empty".to_owned());
    }
    if extension.contains(std::path::MAIN_SEPARATOR)
        || extension.contains('/')
        || extension.contains('\\')
    {
        return Err("extension must not contain a path separator".to_owned());
    }
    Ok(extension)
}

/// Parses and validates a glob pattern.
pub(super) fn parse_glob(value: &str) -> Result<String, String> {
    globset::Glob::new(value)
        .map(|_| value.to_owned())
        .map_err(|error| error.to_string())
}

/// Parses a positive integer.
pub(super) fn parse_positive_usize(value: &str) -> Result<usize, String> {
    let value = value.parse::<usize>().map_err(|error| error.to_string())?;
    if value == 0 {
        return Err("value must be at least 1".to_owned());
    }
    Ok(value)
}
