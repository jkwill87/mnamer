//! Verifies configuration defaults, normalization, and validation.

use super::*;
use crate::config::{ConfigError, STARTER_CONFIG};

#[test]
fn starter_config_matches_built_in_defaults() {
    let parsed = Config::parse_toml(STARTER_CONFIG).unwrap();
    assert_eq!(parsed, Config::default());
    assert_eq!(parsed.cache.ttl_days, 6);
    assert_eq!(parsed.cache.ttl(), Duration::from_secs(6 * 24 * 60 * 60));
}

#[test]
fn cache_ttl_days_round_trips_as_an_integer() {
    let config = Config::parse_toml("[cache]\nttl_days = 14\n").unwrap();
    assert_eq!(config.cache.ttl_days, 14);
    assert_eq!(config.cache.ttl(), Duration::from_secs(14 * 24 * 60 * 60));

    let serialized = toml::to_string(&config).unwrap();
    assert!(serialized.contains("ttl_days = 14"));
    assert_eq!(Config::parse_toml(&serialized).unwrap(), config);
}

#[test]
fn rejects_non_integer_cache_ttl_days_and_legacy_key() {
    for source in [
        "[cache]\nttl_days = -1\n",
        "[cache]\nttl_days = \"6\"\n",
        "[cache]\nttl = \"6d\"\n",
    ] {
        let error = Config::parse_toml(source).unwrap_err();
        assert!(matches!(error, ConfigError::Parse { .. }));
    }
}

#[test]
fn partial_files_use_section_defaults_without_layering() {
    let config = Config::parse_toml(
        r#"
        [matching]
        language = "fr"

        [movie]
        provider = "omdb"
        "#,
    )
    .unwrap();

    assert_eq!(config.matching.language, "fr");
    assert_eq!(config.matching.max_results, 5);
    assert!(!config.matching.allow_guess);
    assert_eq!(config.movie.provider, MovieProvider::Omdb);
    assert_eq!(config.movie.format, Config::default().movie.format);
    assert_eq!(config.episode, EpisodeConfig::default());
    assert!(config.inspection.file_content);
}

#[test]
fn file_content_inspection_defaults_on_and_can_be_disabled() {
    assert!(Config::default().inspection.file_content);
    let config = Config::parse_toml("[inspection]\nfile_content = false\n").unwrap();
    assert!(!config.inspection.file_content);
}

#[test]
fn normalizes_and_stably_deduplicates_extensions() {
    let config = Config::parse_toml(
        r#"
        [discovery]
        extensions = [".MKV", "mkv", " Mp4 ", ".AVI"]
        "#,
    )
    .unwrap();
    assert_eq!(config.discovery.extensions, ["mkv", "mp4", "avi"]);
}

#[test]
fn rejects_unknown_top_level_and_nested_fields() {
    for source in [
        "unexpected = true",
        "[matching]\nmax_result = 5",
        "[inspection]\ncontent = true",
        "[api_keys]\ntvmaze = \"unused\"",
    ] {
        let error = Config::parse_toml(source).unwrap_err();
        assert!(matches!(error, ConfigError::Parse { .. }));
        assert!(error.to_string().contains("unknown field"));
    }
}

#[test]
fn rejects_semantically_invalid_values() {
    let invalid = [
        ("[matching]\nlanguage = \" \"", "matching.language"),
        ("[matching]\nmax_results = 0", "matching.max_results"),
        ("[execution]\njobs = 0", "execution.jobs"),
        ("[execution]\njobs = 33", "execution.jobs"),
        ("[cache]\nttl_days = 0", "cache.ttl_days"),
        (
            "[discovery]\nextensions = [\"/mkv\"]",
            "discovery.extensions",
        ),
        ("[discovery]\nignore = [\"[\"]", "discovery.ignore"),
        ("[movie]\nformat = \"{{\"", "movie.format"),
        ("[episode]\ndirectory = \" \"", "episode.directory"),
        ("[api_keys]\ntmdb = \" \"", "api_keys.tmdb"),
    ];

    for (source, field) in invalid {
        let error = Config::parse_toml(source).unwrap_err();
        assert!(
            error.to_string().contains(field),
            "{error:?} did not name {field}"
        );
    }
}

#[test]
fn parses_plain_provider_api_keys() {
    let config = Config::parse_toml(
        r#"
        [api_keys]
        tmdb = "tmdb-key"
        omdb = "omdb-key"
        tvdb = "tvdb-key"
        "#,
    )
    .unwrap();

    assert_eq!(config.api_keys.tmdb.as_deref(), Some("tmdb-key"));
    assert_eq!(config.api_keys.omdb.as_deref(), Some("omdb-key"));
    assert_eq!(config.api_keys.tvdb.as_deref(), Some("tvdb-key"));
    assert_eq!(config.api_keys.get(ProviderKind::Tvmaze), None);
    assert!(format!("{config:?}").contains("tmdb-key"));
    assert!(serde_json::to_string(&config).unwrap().contains("omdb-key"));
}

#[test]
fn rejects_unknown_upon_functions_during_config_validation() {
    let error =
        Config::parse_toml("[movie]\nformat = \"{{ name | totally_unknown }}.{{ extension }}\"\n")
            .unwrap_err();

    assert!(matches!(error, ConfigError::InvalidValue { .. }));
}
