//! Verifies application command orchestration and rendering.

use super::*;
use crate::cli::Cli;
use crate::cli::MediaMode;
use crate::config::{Config, ConfigLoader, ConfigPaths};
use crate::media::MediaKind;
use crate::net::endpoint::ApiClient;
use crate::net::provider::ProviderKind;
use execution::media_kind;
use provider_setup::configured_registry;

#[test]
fn configured_registry_reports_resolved_credential_sources() {
    let client = ApiClient::without_cache().unwrap();

    let (_, sources) = configured_registry(client, &Config::default());

    assert!(sources[&ProviderKind::Tmdb].is_some());
    assert!(sources[&ProviderKind::Omdb].is_some());
    assert!(sources[&ProviderKind::Tvdb].is_some());
    assert_eq!(sources[&ProviderKind::Tvmaze], None);
}

#[test]
fn media_mode_conversion_preserves_auto_and_hints() {
    assert_eq!(media_kind(MediaMode::Auto), None);
    assert_eq!(media_kind(MediaMode::Movie), Some(MediaKind::Movie));
    assert_eq!(media_kind(MediaMode::Episode), Some(MediaKind::Episode));
}

#[tokio::test]
async fn application_context_honors_injected_cache_path_for_commands_and_processing() {
    let temporary = tempfile::tempdir().unwrap();
    let cache = temporary.path().join("custom-cache");
    let empty = temporary.path().join("empty");
    std::fs::create_dir(&empty).unwrap();
    let context = ApplicationContext::new(ConfigLoader::new(ConfigPaths::new(
        temporary.path(),
        None,
        Some(cache.clone()),
    )));

    let cli = Cli::try_parse_validated_from(["mnamer", "cache", "path"]).unwrap();
    let output = run_with_context(&cli, &context).await.unwrap();
    let ApplicationOutput::Generic { result, .. } = output else {
        panic!("cache path returned a processing result");
    };
    assert_eq!(result.data["path"], cache.to_string_lossy().as_ref());

    let cli = Cli::try_parse_validated_from(["mnamer", "cache", "clear"]).unwrap();
    let output = run_with_context(&cli, &context).await.unwrap();
    let ApplicationOutput::Generic { result, .. } = output else {
        panic!("cache clear returned a processing result");
    };
    assert_eq!(result.data["path"], cache.to_string_lossy().as_ref());

    let cli = Cli::try_parse_validated_from([
        "mnamer",
        "--json",
        "move",
        "--test",
        empty.to_str().unwrap(),
    ])
    .unwrap();
    let output = run_with_context(&cli, &context).await.unwrap();
    let ApplicationOutput::Execution { result, .. } = output else {
        panic!("move returned a maintenance result");
    };
    assert_eq!(result.status, crate::cli::output::CommandStatus::Empty);
}

#[tokio::test]
async fn cache_disabled_commands_do_not_require_a_cache_directory() {
    let temporary = tempfile::tempdir().unwrap();
    let empty = temporary.path().join("empty");
    std::fs::create_dir(&empty).unwrap();
    let context = ApplicationContext::new(ConfigLoader::new(ConfigPaths::new(
        temporary.path(),
        None,
        None,
    )));

    let cli = Cli::try_parse_validated_from(["mnamer", "provider", "list"]).unwrap();
    assert!(matches!(
        run_with_context(&cli, &context).await.unwrap(),
        ApplicationOutput::Generic { .. }
    ));

    let cli = Cli::try_parse_validated_from([
        "mnamer",
        "--json",
        "move",
        "--test",
        "--no-cache",
        empty.to_str().unwrap(),
    ])
    .unwrap();
    let output = run_with_context(&cli, &context).await.unwrap();
    let ApplicationOutput::Execution { result, .. } = output else {
        panic!("move returned a maintenance result");
    };
    assert_eq!(result.status, crate::cli::output::CommandStatus::Empty);
}
