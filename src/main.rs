//! Runs the mnamer command-line application.

use clap::error::ErrorKind;
use mnamer::app::{ApplicationError, run};
use mnamer::cli::Cli;
use mnamer::cli::output::{CommandResult, CommandStatus, ErrorData, render_json};
use std::io::IsTerminal;
use std::process::ExitCode;

/// The main entry point for the mnamer CLI.
#[tokio::main]
async fn main() -> ExitCode {
    let arguments = std::env::args_os().collect::<Vec<_>>();
    let json_requested = arguments.iter().any(|argument| argument == "--json");
    let cli = match Cli::try_parse_validated_from(arguments) {
        Ok(cli) => cli,
        Err(error) => return render_clap_error(error, json_requested),
    };
    initialize_tracing(cli.verbose);
    match run(&cli).await {
        Ok(output) => {
            match output.render(
                cli.json,
                std::io::stdout().is_terminal(),
                std::io::stdout().lock(),
            ) {
                Ok(()) => ExitCode::from(output.exit_code()),
                Err(error) => render_application_error(
                    &cli,
                    ApplicationError::Operational(format!(
                        "could not write command output: {error}"
                    )),
                ),
            }
        }
        Err(error) => render_application_error(&cli, error),
    }
}

fn render_clap_error(error: clap::Error, json_requested: bool) -> ExitCode {
    if matches!(
        error.kind(),
        ErrorKind::DisplayHelp | ErrorKind::DisplayVersion
    ) {
        let code = error.exit_code();
        let _ = error.print();
        return ExitCode::from(u8::try_from(code).unwrap_or(0));
    }
    if json_requested {
        let result = CommandResult::new(
            "mnamer",
            CommandStatus::Error,
            ErrorData {
                kind: "usage".into(),
                message: error.to_string().trim().into(),
            },
        );
        let _ = render_json(&result, std::io::stderr().lock());
    } else {
        let _ = error.print();
    }
    ExitCode::from(2)
}

fn render_application_error(cli: &Cli, error: ApplicationError) -> ExitCode {
    if cli.json {
        let _ = render_json(
            &error.as_result(cli.command.name()),
            std::io::stderr().lock(),
        );
    } else {
        eprintln!("error: {error}");
    }
    ExitCode::from(error.exit_code())
}

fn initialize_tracing(verbosity: u8) {
    let level = match verbosity {
        0 => "warn",
        1 => "info",
        2 => "debug",
        _ => "trace",
    };
    let _ = tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new(level)),
        )
        .with_writer(std::io::stderr)
        .with_ansi(false)
        .try_init();
}
