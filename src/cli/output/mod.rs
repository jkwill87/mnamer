//! Defines typed command outcomes and JSON rendering.

use serde::{Deserialize, Serialize};
use std::io::{self, Write};

pub(crate) mod path;

/// Version of the public JSON command-result envelope.
pub const JSON_SCHEMA_VERSION: u8 = 1;

/// Overall result of an operational command.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum CommandStatus {
    /// The complete command succeeded.
    Ok,
    /// The command succeeded but found no applicable input.
    Empty,
    /// Some requested targets or provider checks failed.
    Partial,
    /// The command could not produce a useful result.
    Error,
}

impl CommandStatus {
    /// Returns the process exit code for a completed operational command.
    pub const fn exit_code(self) -> u8 {
        match self {
            Self::Ok | Self::Empty => 0,
            Self::Partial | Self::Error => 1,
        }
    }
}

/// Public, versioned command envelope used by every renderer.
#[derive(Debug, Serialize)]
pub struct CommandResult<T> {
    /// Public JSON schema version.
    pub schema_version: u8,
    /// Stable kebab-case command name.
    pub command: String,
    /// Overall command status.
    pub status: CommandStatus,
    /// Command-specific payload.
    pub data: T,
    /// Non-fatal diagnostics.
    pub warnings: Vec<String>,
}

impl<T> CommandResult<T> {
    /// Creates a schema-versioned result.
    pub fn new(command: impl Into<String>, status: CommandStatus, data: T) -> Self {
        Self {
            schema_version: JSON_SCHEMA_VERSION,
            command: command.into(),
            status,
            data,
            warnings: Vec::new(),
        }
    }

    /// Appends one non-fatal warning.
    #[must_use]
    pub fn with_warning(mut self, warning: impl Into<String>) -> Self {
        self.warnings.push(warning.into());
        self
    }

    /// Returns the operational exit code represented by this result.
    pub const fn exit_code(&self) -> u8 {
        self.status.exit_code()
    }
}

/// A structured fatal error document for recognized JSON invocations.
#[derive(Debug, Serialize)]
pub struct ErrorData {
    /// Stable error category.
    pub kind: String,
    /// Human-readable explanation that never contains credentials.
    pub message: String,
}

/// Writes exactly one compact JSON document followed by a newline.
pub fn render_json<T: Serialize>(
    result: &CommandResult<T>,
    mut writer: impl Write,
) -> io::Result<()> {
    let mut document = serde_json::to_vec(result)?;
    document.push(b'\n');
    writer.write_all(&document)
}

crate::unit_tests!("mod.test.rs");
