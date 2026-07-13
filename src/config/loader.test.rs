//! Verifies configuration discovery, initialization, and persistence.

use super::*;
use std::fs;
use tempfile::TempDir;

fn write(path: &Path, contents: &str) {
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, contents).unwrap();
}

fn language_config(language: &str) -> String {
    format!("[matching]\nlanguage = {language:?}\n")
}

#[test]
fn explicit_config_has_priority_and_relative_paths_use_injected_cwd() {
    let temp = TempDir::new().unwrap();
    let cwd = temp.path().join("work/project");
    let user_dir = temp.path().join("user");
    fs::create_dir_all(&cwd).unwrap();
    write(&cwd.join(CONFIG_FILENAME), &language_config("de"));
    write(&user_dir.join(CONFIG_FILENAME), &language_config("es"));
    write(&cwd.join("explicit.toml"), &language_config("fr"));
    let loader = ConfigLoader::new(ConfigPaths::new(
        &cwd,
        Some(user_dir),
        Some(temp.path().join("cache")),
    ));

    let loaded = loader
        .load(Some(Path::new("explicit.toml")))
        .unwrap();
    assert_eq!(loaded.config.matching.language, "fr");
    assert_eq!(
        loaded.origin.path(),
        Some(cwd.join("explicit.toml").as_path())
    );
    assert!(matches!(loaded.origin, ConfigOrigin::Explicit { .. }));
}

#[test]
fn upward_discovery_selects_only_the_nearest_file() {
    let temp = TempDir::new().unwrap();
    let root = temp.path().join("root");
    let cwd = root.join("one/two/three");
    fs::create_dir_all(&cwd).unwrap();
    write(&root.join(CONFIG_FILENAME), &language_config("de"));
    write(
        &root.join("one/two").join(CONFIG_FILENAME),
        &language_config("it"),
    );
    let loader = ConfigLoader::new(ConfigPaths::new(&cwd, None, None));

    let loaded = loader.load(None).unwrap();
    assert_eq!(loaded.config.matching.language, "it");
    assert_eq!(
        loaded.origin.path(),
        Some(root.join("one/two").join(CONFIG_FILENAME).as_path())
    );
    assert!(matches!(loaded.origin, ConfigOrigin::Local { .. }));
}

#[test]
fn invalid_nearest_file_is_an_error_instead_of_falling_back() {
    let temp = TempDir::new().unwrap();
    let root = temp.path().join("root");
    let cwd = root.join("project/nested");
    let user_dir = temp.path().join("user");
    fs::create_dir_all(&cwd).unwrap();
    write(&root.join(CONFIG_FILENAME), &language_config("de"));
    write(
        &root.join("project").join(CONFIG_FILENAME),
        "unknown = true",
    );
    write(&user_dir.join(CONFIG_FILENAME), &language_config("fr"));
    let loader = ConfigLoader::new(ConfigPaths::new(&cwd, Some(user_dir), None));

    let error = loader.load(None).unwrap_err();
    assert!(matches!(error, ConfigError::Parse { .. }));
}

#[test]
fn uses_user_file_then_defaults_when_no_local_file_exists() {
    let temp = TempDir::new().unwrap();
    let cwd = temp.path().join("work");
    let user_dir = temp.path().join("user");
    fs::create_dir_all(&cwd).unwrap();
    write(&user_dir.join(CONFIG_FILENAME), &language_config("ja"));
    let loader = ConfigLoader::new(ConfigPaths::new(&cwd, Some(user_dir.clone()), None));

    let loaded = loader.load(None).unwrap();
    assert_eq!(loaded.config.matching.language, "ja");
    assert!(matches!(loaded.origin, ConfigOrigin::User { .. }));

    fs::remove_file(user_dir.join(CONFIG_FILENAME)).unwrap();
    let loaded = loader.load(None).unwrap();
    assert_eq!(loaded.config, Config::default());
    assert_eq!(loaded.origin, ConfigOrigin::Defaults);
}

#[test]
fn missing_explicit_config_is_an_error() {
    let temp = TempDir::new().unwrap();
    let loader = ConfigLoader::new(ConfigPaths::new(temp.path(), None, None));
    let error = loader
        .load(Some(Path::new("missing.toml")))
        .unwrap_err();
    assert!(matches!(error, ConfigError::Read { .. }));
}

#[test]
fn validates_an_explicit_file() {
    let temp = TempDir::new().unwrap();
    write(&temp.path().join("valid.toml"), &language_config("de"));
    let loader = ConfigLoader::new(ConfigPaths::new(temp.path(), None, None));
    let config = loader.validate_path(Path::new("valid.toml")).unwrap();
    assert_eq!(config.matching.language, "de");
}

#[test]
fn initializes_os_native_target_without_replacing_by_default() {
    let temp = TempDir::new().unwrap();
    let cwd = temp.path().join("work");
    let user_dir = temp.path().join("config");
    let cache_dir = temp.path().join("cache/provider-responses");
    fs::create_dir_all(&cwd).unwrap();
    let loader = ConfigLoader::new(ConfigPaths::new(
        &cwd,
        Some(user_dir.clone()),
        Some(cache_dir.clone()),
    ));

    assert_eq!(loader.paths().cache_dir(), Some(cache_dir.as_path()));
    let path = loader.initialize(None, false).unwrap();
    assert_eq!(path, user_dir.join(CONFIG_FILENAME));
    assert_eq!(fs::read_to_string(&path).unwrap(), STARTER_CONFIG);
    assert_eq!(loader.validate_path(&path).unwrap(), Config::default());

    assert!(matches!(
        loader.initialize(None, false),
        Err(ConfigError::AlreadyExists { .. })
    ));
    fs::write(&path, "broken").unwrap();
    loader.initialize(None, true).unwrap();
    assert_eq!(fs::read_to_string(path).unwrap(), STARTER_CONFIG);
}

#[test]
fn initializes_explicit_relative_target_and_creates_parents() {
    let temp = TempDir::new().unwrap();
    let cwd = temp.path().join("work");
    fs::create_dir_all(&cwd).unwrap();
    let loader = ConfigLoader::new(ConfigPaths::new(&cwd, None, None));

    let path = loader
        .initialize(Some(Path::new("nested/custom.toml")), false)
        .unwrap();
    assert_eq!(path, cwd.join("nested/custom.toml"));
    assert_eq!(fs::read_to_string(path).unwrap(), STARTER_CONFIG);
}

#[test]
fn init_without_os_directory_is_a_clear_error() {
    let temp = TempDir::new().unwrap();
    let loader = ConfigLoader::new(ConfigPaths::new(temp.path(), None, None));
    assert!(matches!(
        loader.initialize(None, false),
        Err(ConfigError::NoProjectDirectory)
    ));
}

#[test]
fn loaded_configuration_serialization_includes_origin_and_plain_keys() {
    let loaded = LoadedConfig {
        config: Config::parse_toml("[api_keys]\nomdb = \"visible\"").unwrap(),
        origin: ConfigOrigin::Explicit {
            path: PathBuf::from("mnamer.toml"),
        },
    };
    let json = serde_json::to_string(&loaded).unwrap();
    assert!(json.contains("explicit"));
    assert!(json.contains("mnamer.toml"));
    assert!(json.contains("visible"));
    assert!(loaded.config.to_toml().unwrap().contains("visible"));
}
