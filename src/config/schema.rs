//! Defines the strict configuration schema, defaults, normalization, and validation.

use crate::media::MediaFormat;
use crate::net::provider::ProviderKind;
use clap::ValueEnum;
use serde::{Deserialize, Serialize};
use std::{collections::HashSet, path::PathBuf, time::Duration};

/// Number of seconds in one cache TTL day.
const SECONDS_PER_DAY: u64 = 24 * 60 * 60;

/// Complete configuration loaded from one `mnamer.toml` file or defaults.
#[derive(Clone, Debug, Default, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct Config {
    /// File discovery configuration.
    pub discovery: DiscoveryConfig,
    /// Media file inspection configuration.
    pub inspection: InspectionConfig,
    /// Provider matching configuration.
    pub matching: MatchingConfig,
    /// Batch execution configuration.
    pub execution: ExecutionConfig,
    /// Generated-path formatting configuration.
    pub formatting: FormattingConfig,
    /// Movie provider and destination configuration.
    pub movie: MovieConfig,
    /// Episode provider and destination configuration.
    pub episode: EpisodeConfig,
    /// Provider-response cache configuration.
    pub cache: CacheConfig,
    /// Optional provider API keys.
    pub api_keys: ApiKeys,
}

/// Media file inspection settings.
#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct InspectionConfig {
    /// Whether supported media containers are inspected for technical metadata.
    pub file_content: bool,
}

impl Default for InspectionConfig {
    fn default() -> Self {
        Self { file_content: true }
    }
}

impl Config {
    /// Normalizes configuration values in place.
    pub(super) fn normalize(&mut self) {
        let mut seen = HashSet::new();
        self.discovery.extensions = self
            .discovery
            .extensions
            .drain(..)
            .map(|extension| normalize_extension(&extension))
            .filter(|extension| seen.insert(extension.clone()))
            .collect();
    }
}

/// Optional API keys for providers that require authentication.
#[derive(Clone, Debug, Default, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct ApiKeys {
    /// The Movie Database API key.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tmdb: Option<String>,
    /// The Open Movie Database API key.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub omdb: Option<String>,
    /// TheTVDB API key.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tvdb: Option<String>,
}

impl ApiKeys {
    /// Returns the configured key for an authenticated provider.
    pub fn get(&self, provider: ProviderKind) -> Option<&str> {
        match provider {
            ProviderKind::Tmdb => self.tmdb.as_deref(),
            ProviderKind::Omdb => self.omdb.as_deref(),
            ProviderKind::Tvdb => self.tvdb.as_deref(),
            ProviderKind::Tvmaze => None,
        }
    }
}

/// File discovery settings.
#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct DiscoveryConfig {
    /// Whether directory traversal is recursive.
    pub recursive: bool,
    /// Case-insensitive extensions eligible for discovery, without leading dots.
    pub extensions: Vec<String>,
    /// Case-insensitive glob patterns excluded from discovery.
    pub ignore: Vec<String>,
}

impl Default for DiscoveryConfig {
    fn default() -> Self {
        Self {
            recursive: false,
            extensions: ["avi", "m4v", "mp4", "mkv", "ts", "wmv"]
                .into_iter()
                .chain(
                    MediaFormat::ALL
                        .into_iter()
                        .filter(|format| format.is_subtitle())
                        .map(MediaFormat::extension),
                )
                .map(str::to_owned)
                .collect(),
            ignore: vec!["**/*sample*".into()],
        }
    }
}

/// Metadata matching settings.
#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct MatchingConfig {
    /// Provider response language.
    pub language: String,
    /// Maximum provider results shown or considered.
    pub max_results: usize,
    /// Whether batch processing may use filename metadata after a provider miss.
    pub allow_guess: bool,
}

impl Default for MatchingConfig {
    fn default() -> Self {
        Self {
            language: "en".to_owned(),
            max_results: 5,
            allow_guess: false,
        }
    }
}

/// Batch execution settings.
#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct ExecutionConfig {
    /// Maximum concurrent metadata-resolution jobs.
    pub jobs: u8,
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self { jobs: 4 }
    }
}

/// Generated-path formatting settings.
#[derive(Clone, Copy, Debug, Default, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct FormattingConfig {
    /// Whether generated paths are lowercased.
    pub lowercase: bool,
    /// Whether generated paths use scene conventions.
    pub scene: bool,
}

/// Movie provider and destination settings.
#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct MovieConfig {
    /// Movie metadata provider.
    pub provider: MovieProvider,
    /// Movie filename template.
    pub format: String,
    /// Optional movie destination-directory template.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub directory: Option<String>,
}

impl Default for MovieConfig {
    fn default() -> Self {
        Self {
            provider: MovieProvider::Tmdb,
            format: "{{ name }} ({{ year }}).{{ extension }}".to_owned(),
            directory: None,
        }
    }
}

/// Episode provider and destination settings.
#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct EpisodeConfig {
    /// Episode metadata provider.
    pub provider: EpisodeProvider,
    /// Episode filename template.
    pub format: String,
    /// Optional episode destination-directory template.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub directory: Option<String>,
}

impl Default for EpisodeConfig {
    fn default() -> Self {
        Self {
            provider: EpisodeProvider::Tvmaze,
            format: "{{ series }} - S{{ season | pad: 2 }}E{{ episode | pad: 2 }} - {{ title }}.{{ extension }}"
                .to_owned(),
            directory: None,
        }
    }
}

/// Provider-response cache settings.
#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(default, deny_unknown_fields)]
pub struct CacheConfig {
    /// Whether ordinary provider requests use the persistent cache.
    pub enabled: bool,
    /// Whole-day lifetime of successful cached provider responses.
    pub ttl_days: u32,
}

impl CacheConfig {
    /// Returns the configured cache lifetime as a duration.
    pub(crate) fn ttl(&self) -> Duration {
        Duration::from_secs(u64::from(self.ttl_days) * SECONDS_PER_DAY)
    }
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            ttl_days: 6,
        }
    }
}

/// Supported movie metadata providers.
#[derive(Clone, Copy, Debug, Default, Deserialize, PartialEq, Eq, Serialize, ValueEnum)]
#[serde(rename_all = "lowercase")]
pub enum MovieProvider {
    /// The Movie Database.
    #[default]
    Tmdb,
    /// The Open Movie Database.
    Omdb,
}

impl From<MovieProvider> for ProviderKind {
    fn from(provider: MovieProvider) -> Self {
        match provider {
            MovieProvider::Tmdb => Self::Tmdb,
            MovieProvider::Omdb => Self::Omdb,
        }
    }
}

/// Supported episode metadata providers.
#[derive(Clone, Copy, Debug, Default, Deserialize, PartialEq, Eq, Serialize, ValueEnum)]
#[serde(rename_all = "lowercase")]
pub enum EpisodeProvider {
    /// TVmaze.
    #[default]
    Tvmaze,
    /// TheTVDB version 3 API.
    Tvdb,
}

impl From<EpisodeProvider> for ProviderKind {
    fn from(provider: EpisodeProvider) -> Self {
        match provider {
            EpisodeProvider::Tvmaze => Self::Tvmaze,
            EpisodeProvider::Tvdb => Self::Tvdb,
        }
    }
}

/// Describes one configuration validation failure.
pub(super) struct ValidationError {
    /// Stores the configuration field name.
    pub(super) field: String,
    /// Stores the diagnostic message.
    pub(super) message: String,
}

impl ValidationError {
    /// Creates a configuration validation failure.
    fn new(field: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            field: field.into(),
            message: message.into(),
        }
    }
}

/// Validates normalized configuration values.
pub(super) fn validate(config: &Config) -> Result<(), ValidationError> {
    if mediakit::meta::fields::Language::from_identifier(config.matching.language.trim()).is_none()
    {
        return Err(ValidationError::new(
            "matching.language",
            "must be a supported language name or ISO 639 code",
        ));
    }
    if config.matching.max_results == 0 {
        return Err(ValidationError::new(
            "matching.max_results",
            "must be at least 1",
        ));
    }
    if !(1..=32).contains(&config.execution.jobs) {
        return Err(ValidationError::new(
            "execution.jobs",
            "must be between 1 and 32",
        ));
    }
    if config.cache.ttl_days == 0 {
        return Err(ValidationError::new(
            "cache.ttl_days",
            "must be greater than zero",
        ));
    }

    for extension in &config.discovery.extensions {
        validate_extension(extension)
            .map_err(|message| ValidationError::new("discovery.extensions", message))?;
    }
    for pattern in &config.discovery.ignore {
        globset::Glob::new(pattern)
            .map_err(|error| ValidationError::new("discovery.ignore", error.to_string()))?;
    }

    validate_template_syntax("movie.format", &config.movie.format)?;
    validate_optional_template_syntax("movie.directory", config.movie.directory.as_deref())?;
    validate_template_syntax("episode.format", &config.episode.format)?;
    validate_optional_template_syntax("episode.directory", config.episode.directory.as_deref())?;
    crate::execute::format::DestinationFormatter::new(crate::execute::format::FormatOptions {
        movie_format: config.movie.format.clone(),
        episode_format: config.episode.format.clone(),
        movie_directory: config.movie.directory.as_ref().map(PathBuf::from),
        episode_directory: config.episode.directory.as_ref().map(PathBuf::from),
        lowercase: config.formatting.lowercase,
        scene: config.formatting.scene,
    })
    .map_err(|error| ValidationError::new("formatting", error.to_string()))?;

    for provider in [ProviderKind::Tmdb, ProviderKind::Omdb, ProviderKind::Tvdb] {
        if config
            .api_keys
            .get(provider)
            .is_some_and(|key| key.trim().is_empty())
        {
            return Err(ValidationError::new(
                format!("api_keys.{provider}"),
                "must not be empty",
            ));
        }
    }
    Ok(())
}

/// Normalizes a configured file extension.
fn normalize_extension(extension: &str) -> String {
    extension
        .trim()
        .trim_start_matches('.')
        .to_ascii_lowercase()
}

/// Validates one configured file extension.
fn validate_extension(extension: &str) -> Result<(), String> {
    if extension.is_empty() {
        return Err("extensions must not be empty".to_owned());
    }
    if extension.contains('/') || extension.contains('\\') {
        return Err("extensions must not contain path separators".to_owned());
    }
    Ok(())
}

/// Validates one required destination template.
fn validate_template_syntax(field: &str, template: &str) -> Result<(), ValidationError> {
    if template.trim().is_empty() {
        return Err(ValidationError::new(field, "must not be empty"));
    }
    upon::Engine::new()
        .compile(template)
        .map(|_| ())
        .map_err(|error| ValidationError::new(field, error.to_string()))
}

/// Validates one optional destination template.
fn validate_optional_template_syntax(
    field: &str,
    template: Option<&str>,
) -> Result<(), ValidationError> {
    template.map_or(Ok(()), |template| validate_template_syntax(field, template))
}

crate::unit_tests!("schema.test.rs");
