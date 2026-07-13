//! Executes version-reporting commands.

use super::result::{ApplicationError, ApplicationOutput, generic_ok};
use serde_json::json;

/// Runs the version-reporting command.
pub(super) fn run() -> Result<ApplicationOutput, ApplicationError> {
    let version = env!("CARGO_PKG_VERSION");
    generic_ok(
        "version",
        json!({"version": version}),
        vec![format!("mnamer {version}")],
    )
}
