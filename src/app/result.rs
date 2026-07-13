//! Defines and renders command orchestration outcomes.

use crate::cli::output::{CommandResult, CommandStatus, ErrorData, render_json};
use crate::cli::prompt;
use crate::config::ConfigError;
use crate::execute::output::{ExecutionData, render_execution_human_colored};
use serde_json::Value;
use std::io::{self, Write};

/// Fully rendered result category returned by command orchestration.
pub enum ApplicationOutput {
    /// Filesystem execution output with typed per-item outcomes.
    Execution {
        /// Versioned command result.
        result: CommandResult<ExecutionData>,
        /// Process exit code, including the interrupt override.
        exit_code: u8,
        /// Whether the human result continues an interactive cliclack session.
        interactive: bool,
    },
    /// Maintenance-command output.
    Generic {
        /// Versioned command result.
        result: CommandResult<Value>,
        /// Human-readable lines derived from the same result.
        human: Vec<String>,
        /// Process exit code.
        exit_code: u8,
    },
}

impl ApplicationOutput {
    /// Returns the process exit code selected by the command result.
    pub const fn exit_code(&self) -> u8 {
        match self {
            Self::Execution { exit_code, .. } | Self::Generic { exit_code, .. } => *exit_code,
        }
    }

    /// Renders the result to stdout without allowing command logic to print.
    pub fn render(&self, json_output: bool, color: bool, mut writer: impl Write) -> io::Result<()> {
        match self {
            Self::Execution { result, .. } if json_output => render_json(result, writer),
            Self::Execution {
                result,
                interactive: true,
                ..
            } => prompt::render_result(result),
            Self::Execution { result, .. } => render_execution_human_colored(result, writer, color),
            Self::Generic { result, .. } if json_output => render_json(result, writer),
            Self::Generic { result, human, .. } => {
                for line in human {
                    writeln!(writer, "{line}")?;
                }
                for warning in &result.warnings {
                    writeln!(writer, "warning: {warning}")?;
                }
                Ok(())
            }
        }
    }
}

/// Fatal error category produced before a typed operational result exists.
#[derive(Debug, thiserror::Error)]
pub enum ApplicationError {
    /// Invalid CLI/configuration combination discovered at runtime.
    #[error("{0}")]
    Usage(String),
    /// Configuration selection, parsing, or persistence failed.
    #[error(transparent)]
    Config(#[from] ConfigError),
    /// Operational infrastructure failed before per-item handling was possible.
    #[error("{0}")]
    Operational(String),
}

impl ApplicationError {
    /// Returns the stable JSON error category.
    pub const fn kind(&self) -> &'static str {
        match self {
            Self::Usage(_) => "usage",
            Self::Config(_) => "configuration",
            Self::Operational(_) => "operational",
        }
    }

    /// Returns the public process exit code.
    pub const fn exit_code(&self) -> u8 {
        match self {
            Self::Usage(_) | Self::Config(_) => 2,
            Self::Operational(_) => 1,
        }
    }

    /// Converts the error into the versioned JSON error envelope.
    pub fn as_result(&self, command: &str) -> CommandResult<ErrorData> {
        CommandResult::new(
            command,
            CommandStatus::Error,
            ErrorData {
                kind: self.kind().into(),
                message: self.to_string(),
            },
        )
    }
}

/// Creates an operational application error.
pub(super) fn operational(error: impl std::fmt::Display) -> ApplicationError {
    ApplicationError::Operational(error.to_string())
}

/// Creates a successful generic command result.
pub(super) fn generic_ok(
    command: &str,
    data: Value,
    human: Vec<String>,
) -> Result<ApplicationOutput, ApplicationError> {
    let result = CommandResult::new(command, CommandStatus::Ok, data);
    Ok(ApplicationOutput::Generic {
        exit_code: result.exit_code(),
        result,
        human,
    })
}
