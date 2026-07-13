//! Loads and validates mnamer configuration.

mod loader;
mod schema;

pub use loader::{
    CONFIG_FILENAME, ConfigError, ConfigLoader, ConfigOrigin, ConfigPaths, LoadedConfig,
    STARTER_CONFIG,
};
pub use schema::{
    ApiKeys, CacheConfig, Config, DiscoveryConfig, EpisodeConfig, EpisodeProvider, ExecutionConfig,
    FormattingConfig, InspectionConfig, MatchingConfig, MovieConfig, MovieProvider,
};
