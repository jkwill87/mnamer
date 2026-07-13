//! Defines the top-level command tree and command-family selection.

use super::{CacheCommand, ConfigCommand, ExecutionArgs, ExecutionOptions, ProviderCommand};
use crate::config::Config;
use crate::execute::Action;
use clap::{Parser, Subcommand};
use std::{ffi::OsString, path::PathBuf};

/// The `mnamer` command-line interface.
#[derive(Clone, Debug, Parser, PartialEq, Eq)]
#[command(
    name = "mnamer",
    version,
    disable_version_flag = true,
    disable_help_flag = true,
    about = "A media file renaming and organization utility.",
    subcommand_required = true,
    arg_required_else_help = true
)]
pub struct Cli {
    /// Use one explicit `mnamer.toml` file.
    #[arg(long, global = true, value_name = "PATH")]
    pub config: Option<PathBuf>,

    /// Emit one structured JSON document.
    #[arg(long, global = true)]
    pub json: bool,

    /// Increase diagnostic verbosity; may be repeated.
    #[arg(short = 'v', long, global = true, action = clap::ArgAction::Count)]
    pub verbose: u8,

    /// Operation to perform.
    #[command(subcommand)]
    pub command: Command,
}

impl Cli {
    /// Parses and validates command-line arguments without exiting the process.
    pub fn try_parse_validated_from<I, T>(args: I) -> Result<Self, clap::Error>
    where
        I: IntoIterator<Item = T>,
        T: Into<OsString> + Clone,
    {
        let cli = Self::try_parse_from(args)?;
        cli.validate()
            .map_err(|error| clap::Error::raw(clap::error::ErrorKind::ArgumentConflict, error))?;
        Ok(cli)
    }

    /// Parses and validates command-line arguments, exiting on invalid input.
    pub fn parse_validated() -> Self {
        match Self::try_parse_validated_from(std::env::args_os()) {
            Ok(cli) => cli,
            Err(error) => error.exit(),
        }
    }

    /// Validates rules that span global and subcommand arguments.
    pub fn validate(&self) -> Result<(), CliError> {
        if let Some(args) = self.command.execution_args() {
            args.validate(self.json)?;
        }
        Ok(())
    }

    /// Resolves CLI execution overrides on top of a selected configuration.
    ///
    /// Returns `None` for maintenance commands.
    pub fn execution_options(&self, config: &Config) -> Option<Result<ExecutionOptions, CliError>> {
        self.command.execution_args().map(|args| {
            args.resolve(
                config,
                self.json,
                self.command
                    .action()
                    .expect("execution command has an action"),
                self.command.overwrite(),
            )
        })
    }
}

/// Top-level `mnamer` operations.
#[derive(Clone, Debug, Subcommand, PartialEq, Eq)]
pub enum Command {
    /// Rename media files, moving them to their target locations.
    Move {
        /// Arguments shared by filesystem execution commands.
        #[command(flatten)]
        args: ExecutionArgs,
        /// Permit replacement of existing destination files.
        #[arg(long)]
        overwrite: bool,
    },
    /// Rename media files, copying them to their target locations.
    Copy {
        /// Arguments shared by filesystem execution commands.
        #[command(flatten)]
        args: ExecutionArgs,
        /// Permit replacement of existing destination files.
        #[arg(long)]
        overwrite: bool,
    },
    /// Create hard links at target locations, keeping source files in place.
    #[cfg(not(windows))]
    Hardlink {
        /// Arguments shared by filesystem execution commands.
        #[command(flatten)]
        args: ExecutionArgs,
    },
    /// Create symbolic links at target locations, keeping source files in place.
    #[cfg(not(windows))]
    Symlink {
        /// Arguments shared by filesystem execution commands.
        #[command(flatten)]
        args: ExecutionArgs,
    },
    /// Inspect, validate, or initialize `mnamer.toml`.
    Config {
        /// Configuration operation.
        #[command(subcommand)]
        command: ConfigCommand,
    },
    /// Inspect or clear the provider-response cache.
    Cache {
        /// Cache operation.
        #[command(subcommand)]
        command: CacheCommand,
    },
    /// List or verify metadata providers.
    Provider {
        /// Provider operation.
        #[command(subcommand)]
        command: ProviderCommand,
    },
    /// Display the running mnamer version.
    #[command(display_order = usize::MAX)]
    Version,
}

impl Command {
    /// Returns the arguments for a filesystem execution command.
    pub const fn execution_args(&self) -> Option<&ExecutionArgs> {
        match self {
            Self::Move { args, .. } | Self::Copy { args, .. } => Some(args),
            #[cfg(not(windows))]
            Self::Hardlink { args } | Self::Symlink { args } => Some(args),
            Self::Version | Self::Config { .. } | Self::Cache { .. } | Self::Provider { .. } => {
                None
            }
        }
    }

    /// Returns the selected filesystem action, if any.
    pub const fn action(&self) -> Option<Action> {
        match self {
            Self::Move { .. } => Some(Action::Move),
            Self::Copy { .. } => Some(Action::Copy),
            #[cfg(not(windows))]
            Self::Hardlink { .. } => Some(Action::Hardlink),
            #[cfg(not(windows))]
            Self::Symlink { .. } => Some(Action::Symlink),
            Self::Version | Self::Config { .. } | Self::Cache { .. } | Self::Provider { .. } => {
                None
            }
        }
    }

    /// Returns whether this action may replace an existing destination.
    pub const fn overwrite(&self) -> bool {
        match self {
            Self::Move { overwrite, .. } | Self::Copy { overwrite, .. } => *overwrite,
            _ => false,
        }
    }

    /// Returns the stable command name used by human and JSON renderers.
    pub const fn name(&self) -> &'static str {
        match self {
            Self::Version => "version",
            Self::Move { .. } => "move",
            Self::Copy { .. } => "copy",
            #[cfg(not(windows))]
            Self::Hardlink { .. } => "hardlink",
            #[cfg(not(windows))]
            Self::Symlink { .. } => "symlink",
            Self::Config { .. } => "config",
            Self::Cache { .. } => "cache",
            Self::Provider { .. } => "provider",
        }
    }

    /// Returns the selected nested configuration command, if any.
    pub const fn config_command(&self) -> Option<&ConfigCommand> {
        match self {
            Self::Config { command } => Some(command),
            _ => None,
        }
    }

    /// Returns the selected nested cache command, if any.
    pub const fn cache_command(&self) -> Option<&CacheCommand> {
        match self {
            Self::Cache { command } => Some(command),
            _ => None,
        }
    }

    /// Returns the selected nested provider command, if any.
    pub const fn provider_command(&self) -> Option<&ProviderCommand> {
        match self {
            Self::Provider { command } => Some(command),
            _ => None,
        }
    }
}

/// Cross-option command-line validation failures.
#[derive(Clone, Copy, Debug, thiserror::Error, PartialEq, Eq)]
pub enum CliError {
    /// `--jobs` was used without batch selection or JSON output.
    #[error("--jobs requires --batch or --json")]
    JobsRequireBatch,
}
