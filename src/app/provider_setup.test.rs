//! Verifies provider credential and cache setup.

use super::*;
use std::collections::BTreeMap;

#[test]
fn resolves_toml_environment_and_embedded_keys_in_order() {
    let environment = BTreeMap::from([("API_KEY_TMDB".to_owned(), "environment-key".to_owned())]);
    let lookup = |name: &str| environment.get(name).cloned();
    let mut config = Config::default();
    config.api_keys.tmdb = Some("  toml-key  ".to_owned());

    assert_eq!(
        resolve_api_key(&config, ProviderKind::Tmdb, &lookup),
        Some(("toml-key".to_owned(), CredentialSource::Toml))
    );

    config.api_keys.tmdb = None;
    assert_eq!(
        resolve_api_key(&config, ProviderKind::Tmdb, &lookup),
        Some(("environment-key".to_owned(), CredentialSource::Environment))
    );

    let blank_environment = |_name: &str| Some("  ".to_owned());
    let (key, source) = resolve_api_key(&config, ProviderKind::Tmdb, &blank_environment).unwrap();
    assert_eq!(key, EMBEDDED_TMDB_API_KEY);
    assert_eq!(source, CredentialSource::Embedded);
}

#[test]
fn configured_registry_reports_sources_without_configuring_tvmaze() {
    let client = ApiClient::without_cache().unwrap();
    let config = Config::default();
    let (_, sources) = configured_registry_with(client, &config, |_name| None);

    assert_eq!(
        sources[&ProviderKind::Tmdb],
        Some(CredentialSource::Embedded)
    );
    assert_eq!(
        sources[&ProviderKind::Omdb],
        Some(CredentialSource::Embedded)
    );
    assert_eq!(
        sources[&ProviderKind::Tvdb],
        Some(CredentialSource::Embedded)
    );
    assert_eq!(sources[&ProviderKind::Tvmaze], None);
    assert_eq!(
        ProviderKind::Tvdb.api_key_environment_variable(),
        Some("API_KEY_TVDB")
    );
    assert_eq!(ProviderKind::Tvmaze.api_key_environment_variable(), None);
}
