//! Discovers, parses, initializes, and persists configuration files.

use super::schema::{self, Config};
use directories::ProjectDirs;
use serde::Serialize;
use std::{
    fs::{self, OpenOptions},
    io::{self, Write},
    path::{Path, PathBuf},
};

/// Filename used for discovered and OS-native configuration files.
pub const CONFIG_FILENAME: &str = "mnamer.toml";

/// A documented starter configuration emitted by `mnamer config init`.
pub const STARTER_CONFIG: &str = include_str!("starter.toml");

impl Config {
    /// Parses, normalizes, and semantically validates TOML configuration text.
    pub fn parse_toml(source: &str) -> Result<Self, ConfigError> {
        parse_config(source, Path::new("<memory>"))
    }

    /// Validates semantic constraints not enforced by TOML deserialization.
    pub fn validate(&self) -> Result<(), ConfigError> {
        schema::validate(self)
            .map_err(|error| ConfigError::invalid_value(error.field, error.message))
    }

    /// Returns a TOML representation of the effective configuration.
    pub fn to_toml(&self) -> Result<String, ConfigError> {
        toml::to_string_pretty(self).map_err(|error| ConfigError::Serialize {
            message: error.to_string(),
        })
    }
}

/// Injectable filesystem locations used by configuration discovery and cache commands.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ConfigPaths {
    /// Stores the working directory.
    current_dir: PathBuf,
    /// Stores the optional configuration directory.
    config_dir: Option<PathBuf>,
    /// Stores the optional cache directory.
    cache_dir: Option<PathBuf>,
}

impl ConfigPaths {
    /// Resolves locations from the process working directory and OS conventions.
    pub fn system() -> Result<Self, ConfigError> {
        let current_dir = std::env::current_dir().map_err(ConfigError::CurrentDirectory)?;
        let project_dirs = ProjectDirs::from("", "", "mnamer");
        Ok(Self {
            current_dir,
            config_dir: project_dirs
                .as_ref()
                .map(|directories| directories.config_dir().to_owned()),
            cache_dir: project_dirs
                .as_ref()
                .map(|directories| directories.cache_dir().join("provider-responses")),
        })
    }

    /// Creates explicitly injected locations, primarily for deterministic tests.
    pub fn new(
        current_dir: impl Into<PathBuf>,
        config_dir: Option<PathBuf>,
        cache_dir: Option<PathBuf>,
    ) -> Self {
        Self {
            current_dir: current_dir.into(),
            config_dir,
            cache_dir,
        }
    }

    /// Returns the working directory from which upward discovery begins.
    pub fn current_dir(&self) -> &Path {
        &self.current_dir
    }

    /// Returns the OS-native configuration file path, when available.
    pub fn user_config_path(&self) -> Option<PathBuf> {
        self.config_dir
            .as_ref()
            .map(|directory| directory.join(CONFIG_FILENAME))
    }

    /// Returns the OS-native provider-response cache directory, when available.
    pub fn cache_dir(&self) -> Option<&Path> {
        self.cache_dir.as_deref()
    }

    /// Resolves a path relative to the configured working directory.
    fn resolve_from_current_dir(&self, path: &Path) -> PathBuf {
        if path.is_absolute() {
            path.to_owned()
        } else {
            self.current_dir.join(path)
        }
    }
}

/// Selects, loads, validates, and initializes `mnamer.toml` files.
#[derive(Clone, Debug)]
pub struct ConfigLoader {
    /// Stores the resolved configuration paths.
    paths: ConfigPaths,
}

impl ConfigLoader {
    /// Creates a loader with injected filesystem locations.
    pub const fn new(paths: ConfigPaths) -> Self {
        Self { paths }
    }

    /// Creates a loader using the current process and OS-native locations.
    pub fn system() -> Result<Self, ConfigError> {
        ConfigPaths::system().map(Self::new)
    }

    /// Returns the filesystem locations used by this loader.
    pub const fn paths(&self) -> &ConfigPaths {
        &self.paths
    }

    /// Loads the first selected configuration without layering files.
    pub fn load(&self, explicit: Option<&Path>) -> Result<LoadedConfig, ConfigError> {
        if let Some(path) = explicit {
            let path = self.paths.resolve_from_current_dir(path);
            return load_path(&path, ConfigOrigin::Explicit { path: path.clone() });
        }

        for directory in self.paths.current_dir.ancestors() {
            let path = directory.join(CONFIG_FILENAME);
            if path.try_exists().map_err(|source| ConfigError::Read {
                path: path.clone(),
                source,
            })? {
                return load_path(&path, ConfigOrigin::Local { path: path.clone() });
            }
        }

        if let Some(path) = self.paths.user_config_path()
            && path.try_exists().map_err(|source| ConfigError::Read {
                path: path.clone(),
                source,
            })?
        {
            return load_path(&path, ConfigOrigin::User { path: path.clone() });
        }

        Ok(LoadedConfig {
            config: Config::default(),
            origin: ConfigOrigin::Defaults,
        })
    }

    /// Validates one explicit path relative to the loader's working directory.
    pub fn validate_path(&self, path: &Path) -> Result<Config, ConfigError> {
        let path = self.paths.resolve_from_current_dir(path);
        read_config(&path)
    }

    /// Writes the documented starter configuration and returns its destination.
    pub fn initialize(&self, path: Option<&Path>, force: bool) -> Result<PathBuf, ConfigError> {
        let path = match path {
            Some(path) => self.paths.resolve_from_current_dir(path),
            None => self
                .paths
                .user_config_path()
                .ok_or(ConfigError::NoProjectDirectory)?,
        };

        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|source| ConfigError::Write {
                path: path.clone(),
                source,
            })?;
        }

        let mut options = OpenOptions::new();
        options.write(true);
        if force {
            options.create(true).truncate(true);
        } else {
            options.create_new(true);
        }
        let mut file = options.open(&path).map_err(|source| {
            if source.kind() == io::ErrorKind::AlreadyExists {
                ConfigError::AlreadyExists { path: path.clone() }
            } else {
                ConfigError::Write {
                    path: path.clone(),
                    source,
                }
            }
        })?;
        file.write_all(STARTER_CONFIG.as_bytes())
            .and_then(|()| file.sync_all())
            .map_err(|source| ConfigError::Write {
                path: path.clone(),
                source,
            })?;
        Ok(path)
    }
}

/// The selected configuration and its discovery source.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct LoadedConfig {
    /// Effective configuration.
    pub config: Config,
    /// File or built-in source selected by first-match discovery.
    pub origin: ConfigOrigin,
}

/// Source selected by configuration discovery.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ConfigOrigin {
    /// No file was selected; built-in defaults are active.
    Defaults,
    /// The global `--config` option selected this file.
    Explicit {
        /// Selected path.
        #[serde(serialize_with = "crate::cli::output::path::serialize")]
        path: PathBuf,
    },
    /// Upward discovery selected this nearest file.
    Local {
        /// Selected path.
        #[serde(serialize_with = "crate::cli::output::path::serialize")]
        path: PathBuf,
    },
    /// OS-native application configuration selected this file.
    User {
        /// Selected path.
        #[serde(serialize_with = "crate::cli::output::path::serialize")]
        path: PathBuf,
    },
}

impl ConfigOrigin {
    /// Returns the selected path, or `None` for built-in defaults.
    pub fn path(&self) -> Option<&Path> {
        match self {
            Self::Defaults => None,
            Self::Explicit { path } | Self::Local { path } | Self::User { path } => Some(path),
        }
    }
}

/// Configuration discovery, parsing, validation, or initialization failure.
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    /// The current process directory could not be read.
    #[error("could not determine the current directory: {0}")]
    CurrentDirectory(#[source] io::Error),
    /// A configuration file could not be read.
    #[error("could not read configuration {path}: {source}")]
    Read {
        /// Configuration path.
        path: PathBuf,
        /// Underlying filesystem failure.
        #[source]
        source: io::Error,
    },
    /// A configuration file was not valid TOML or did not match the strict schema.
    #[error("invalid configuration {path} at {line}:{column}: {message}")]
    Parse {
        /// Configuration path.
        path: PathBuf,
        /// One-based line number.
        line: usize,
        /// One-based column number.
        column: usize,
        /// Parser message without a source excerpt.
        message: String,
    },
    /// A parsed configuration value failed semantic validation.
    #[error("invalid configuration value {field}: {message}")]
    InvalidValue {
        /// Dotted configuration field name.
        field: String,
        /// Validation failure description.
        message: String,
    },
    /// The OS did not provide an application configuration directory.
    #[error("the OS-native mnamer configuration directory is unavailable")]
    NoProjectDirectory,
    /// Initialization refused to replace an existing file.
    #[error("configuration {path} already exists; pass --force to replace it")]
    AlreadyExists {
        /// Existing destination path.
        path: PathBuf,
    },
    /// A starter configuration could not be written.
    #[error("could not write configuration {path}: {source}")]
    Write {
        /// Configuration path.
        path: PathBuf,
        /// Underlying filesystem failure.
        #[source]
        source: io::Error,
    },
    /// A configuration could not be serialized.
    #[error("could not serialize configuration: {message}")]
    Serialize {
        /// Serializer failure description.
        message: String,
    },
}

impl ConfigError {
    /// Creates an invalid-configuration-value error.
    fn invalid_value(field: impl Into<String>, message: impl Into<String>) -> Self {
        Self::InvalidValue {
            field: field.into(),
            message: message.into(),
        }
    }
}

/// Loads and validates configuration from one path.
fn load_path(path: &Path, origin: ConfigOrigin) -> Result<LoadedConfig, ConfigError> {
    read_config(path).map(|config| LoadedConfig { config, origin })
}

/// Reads and parses a configuration file.
fn read_config(path: &Path) -> Result<Config, ConfigError> {
    let source = fs::read_to_string(path).map_err(|source| ConfigError::Read {
        path: path.to_owned(),
        source,
    })?;
    parse_config(&source, path)
}

/// Parses and validates configuration source text.
fn parse_config(source: &str, path: &Path) -> Result<Config, ConfigError> {
    let mut config: Config = toml::from_str(source).map_err(|error: toml::de::Error| {
        let (line, column) = error
            .span()
            .map(|span| line_and_column(source, span.start))
            .unwrap_or((1, 1));
        ConfigError::Parse {
            path: path.to_owned(),
            line,
            column,
            message: error.message().to_owned(),
        }
    })?;
    config.normalize();
    config.validate()?;
    Ok(config)
}

/// Converts a byte offset into one-based line and column coordinates.
fn line_and_column(source: &str, offset: usize) -> (usize, usize) {
    let prefix = &source[..offset.min(source.len())];
    let line = prefix.bytes().filter(|byte| *byte == b'\n').count() + 1;
    let column = prefix.rsplit_once('\n').map_or_else(
        || prefix.chars().count() + 1,
        |(_, tail)| tail.chars().count() + 1,
    );
    (line, column)
}

crate::unit_tests!("loader.test.rs");
