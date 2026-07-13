//! Executes configuration maintenance commands.

use super::result::{ApplicationError, ApplicationOutput, generic_ok};
use crate::cli::{Cli, ConfigCommand};
use crate::config::{ConfigLoader, ConfigOrigin};
use serde_json::json;
use std::path::PathBuf;

/// Runs the configuration maintenance command.
pub(super) fn run(
    cli: &Cli,
    loader: &ConfigLoader,
    command: &ConfigCommand,
) -> Result<ApplicationOutput, ApplicationError> {
    match command {
        ConfigCommand::Path => {
            let loaded = loader.load(cli.config.as_deref())?;
            let path = loaded.origin.path().map(PathBuf::from);
            let human = vec![path.as_ref().map_or_else(
                || "built-in defaults".into(),
                |path| path.display().to_string(),
            )];
            generic_ok(
                "config",
                json!({
                    "operation": "path",
                    "path": path.as_deref().map(|path| path.to_string_lossy()),
                    "origin": loaded.origin
                }),
                human,
            )
        }
        ConfigCommand::Show => {
            let loaded = loader.load(cli.config.as_deref())?;
            let source = origin_label(&loaded.origin);
            let config = loaded.config.to_toml()?;
            let data = serde_json::to_value(&loaded)
                .map_err(|error| ApplicationError::Operational(error.to_string()))?;
            generic_ok(
                "config",
                data,
                vec![format!("# source: {source}\n{config}")],
            )
        }
        ConfigCommand::Validate { path } => {
            let (origin, config) = if let Some(path) = path {
                (path.display().to_string(), loader.validate_path(path)?)
            } else {
                let loaded = loader.load(cli.config.as_deref())?;
                (origin_label(&loaded.origin), loaded.config)
            };
            config.validate()?;
            generic_ok(
                "config",
                json!({"operation": "validate", "valid": true, "source": origin}),
                vec![format!("valid: {origin}")],
            )
        }
        ConfigCommand::Init { path, force } => {
            let path = loader.initialize(path.as_deref(), *force)?;
            generic_ok(
                "config",
                json!({"operation": "init", "path": path.to_string_lossy()}),
                vec![format!("created {}", path.display())],
            )
        }
    }
}

/// Formats a configuration-origin label.
fn origin_label(origin: &ConfigOrigin) -> String {
    origin.path().map_or_else(
        || "built-in defaults".into(),
        |path| path.display().to_string(),
    )
}
