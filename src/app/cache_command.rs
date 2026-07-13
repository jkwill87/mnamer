//! Executes cache maintenance commands.

use super::provider_setup::cache_path;
use super::result::{ApplicationError, ApplicationOutput, generic_ok, operational};
use crate::cli::{CacheCommand, Cli};
use crate::config::ConfigLoader;
use crate::net::endpoint::ApiClient;
use serde_json::json;

/// Runs the cache maintenance command.
pub(super) async fn run(
    cli: &Cli,
    loader: &ConfigLoader,
    command: CacheCommand,
) -> Result<ApplicationOutput, ApplicationError> {
    let loaded = loader.load(cli.config.as_deref())?;
    match command {
        CacheCommand::Path => {
            let path = cache_path(loader)?;
            generic_ok(
                "cache",
                json!({"operation": "path", "path": path.to_string_lossy()}),
                vec![path.display().to_string()],
            )
        }
        CacheCommand::Clear => {
            let path = cache_path(loader)?;
            let client = ApiClient::new(path.clone(), loaded.config.cache.ttl(), true)
                .map_err(operational)?;
            client.clear_cache().await.map_err(operational)?;
            generic_ok(
                "cache",
                json!({
                    "operation": "clear",
                    "path": path.to_string_lossy(),
                    "cleared": true
                }),
                vec![format!("cleared {}", path.display())],
            )
        }
    }
}
