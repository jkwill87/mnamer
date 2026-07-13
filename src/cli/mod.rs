//! Parses and validates command-line input.

mod command;
mod execution;
mod maintenance;
pub mod output;
mod values;

pub mod prompt;

pub use command::{Cli, CliError, Command};
pub use execution::{ExecutionArgs, ExecutionOptions};
pub use maintenance::{CacheCommand, ConfigCommand, ProviderCommand};
pub use values::{ExternalId, ExternalIdSource, MediaMode};

crate::unit_tests!("mod.test.rs");
