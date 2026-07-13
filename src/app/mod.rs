//! Orchestrates command execution and application-result rendering.

mod cache_command;
mod config_command;
mod context;
mod execution;
mod provider_command;
mod provider_setup;
mod result;
mod version_command;

use crate::cli::{Cli, Command};

pub use context::ApplicationContext;
pub use result::{ApplicationError, ApplicationOutput};

/// Executes one already-parsed CLI invocation.
pub async fn run(cli: &Cli) -> Result<ApplicationOutput, ApplicationError> {
    if matches!(cli.command, Command::Version) {
        return version_command::run();
    }
    let context = ApplicationContext::system()?;
    run_with_context(cli, &context).await
}

/// Executes one invocation with explicitly supplied runtime dependencies.
pub async fn run_with_context(
    cli: &Cli,
    context: &ApplicationContext,
) -> Result<ApplicationOutput, ApplicationError> {
    let loader = context.loader();
    match &cli.command {
        Command::Version => version_command::run(),
        Command::Config { command } => config_command::run(cli, loader, command),
        Command::Cache { command } => cache_command::run(cli, loader, *command).await,
        Command::Provider { command } => provider_command::run(cli, loader, command).await,
        Command::Move { .. } | Command::Copy { .. } => {
            execution::run(cli, loader, context.candidate_source()).await
        }
        #[cfg(not(windows))]
        Command::Hardlink { .. } | Command::Symlink { .. } => {
            execution::run(cli, loader, context.candidate_source()).await
        }
    }
}

crate::unit_tests!("mod.test.rs");
