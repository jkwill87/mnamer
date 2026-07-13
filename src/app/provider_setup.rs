//! Constructs configured provider registries and response caches.

use super::result::ApplicationError;
use crate::config::{Config, ConfigLoader};
use crate::net::endpoint::ApiClient;
use crate::net::provider::{
    EMBEDDED_OMDB_API_KEY, EMBEDDED_TMDB_API_KEY, EMBEDDED_TVDB_API_KEY, ProviderKind,
    ProviderRegistry,
};
use serde::Serialize;
use std::collections::BTreeMap;
use std::path::PathBuf;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
/// Identifies the source of a resolved provider credential.
pub(super) enum CredentialSource {
    /// Selects a credential from configuration.
    Toml,
    /// Selects a credential from the process environment.
    Environment,
    /// Selects the embedded fallback credential.
    Embedded,
}

/// Resolves the configured response-cache path.
pub(super) fn cache_path(loader: &ConfigLoader) -> Result<PathBuf, ApplicationError> {
    loader
        .paths()
        .cache_dir()
        .map(PathBuf::from)
        .ok_or_else(|| ApplicationError::Operational("cache directory is unavailable".into()))
}

/// Builds a provider registry from resolved configuration.
pub(super) fn configured_registry(
    client: ApiClient,
    config: &Config,
) -> (
    ProviderRegistry,
    BTreeMap<ProviderKind, Option<CredentialSource>>,
) {
    configured_registry_with(client, config, |name| std::env::var(name).ok())
}

/// Builds a provider registry with an injected environment lookup.
fn configured_registry_with<F>(
    client: ApiClient,
    config: &Config,
    environment: F,
) -> (
    ProviderRegistry,
    BTreeMap<ProviderKind, Option<CredentialSource>>,
)
where
    F: Fn(&str) -> Option<String>,
{
    let mut registry = ProviderRegistry::new(client);
    let mut sources = BTreeMap::new();
    for provider in ProviderKind::ALL {
        let key = resolve_api_key(config, provider, &environment);
        sources.insert(provider, key.as_ref().map(|(_, source)| *source));
        if let Some((key, _)) = key {
            registry = registry.with_api_key(provider, key);
        }
    }
    (registry, sources)
}

/// Resolves one provider API key and its source.
fn resolve_api_key<F>(
    config: &Config,
    provider: ProviderKind,
    environment: &F,
) -> Option<(String, CredentialSource)>
where
    F: Fn(&str) -> Option<String>,
{
    if let Some(key) = config.api_keys.get(provider).and_then(nonempty) {
        return Some((key, CredentialSource::Toml));
    }

    if let Some(name) = provider.api_key_environment_variable()
        && let Some(key) = environment(name).and_then(|key| nonempty(&key))
    {
        return Some((key, CredentialSource::Environment));
    }

    embedded_api_key(provider)
        .and_then(nonempty)
        .map(|key| (key, CredentialSource::Embedded))
}

/// Returns the embedded fallback key for a provider.
const fn embedded_api_key(provider: ProviderKind) -> Option<&'static str> {
    match provider {
        ProviderKind::Tmdb => Some(EMBEDDED_TMDB_API_KEY),
        ProviderKind::Omdb => Some(EMBEDDED_OMDB_API_KEY),
        ProviderKind::Tvdb => Some(EMBEDDED_TVDB_API_KEY),
        ProviderKind::Tvmaze => None,
    }
}

/// Normalizes an empty credential to no value.
fn nonempty(value: &str) -> Option<String> {
    let value = value.trim();
    (!value.is_empty()).then(|| value.to_owned())
}

crate::unit_tests!("provider_setup.test.rs");
