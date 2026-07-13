//! Defines and renders filesystem execution results.

use super::{Action, Operation, OperationOutcome};
use crate::cli::output::CommandResult;
use serde::Serialize;
use std::io::{self, Write};

/// Counts for a filesystem execution result.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct ExecutionSummary {
    /// Number of roots explicitly requested.
    pub requested: usize,
    /// Number of media files discovered.
    pub discovered: usize,
    /// Number of operations ready to apply.
    pub ready: usize,
    /// Number of filesystem actions completed.
    pub completed: usize,
    /// Number of already-correct paths.
    pub unchanged: usize,
    /// Number of failed or skipped requested targets.
    pub failed: usize,
}

impl ExecutionSummary {
    /// Builds a summary from final per-operation outcomes.
    pub fn from_operations(requested: usize, operations: &[Operation]) -> Self {
        Self::from_operations_with_discovered(requested, operations.len(), operations)
    }

    /// Builds a summary while keeping non-file discovery failures out of the
    /// discovered-media count.
    pub fn from_operations_with_discovered(
        requested: usize,
        discovered: usize,
        operations: &[Operation],
    ) -> Self {
        let mut summary = Self {
            requested,
            discovered,
            ..Self::default()
        };
        for operation in operations {
            match operation.outcome {
                OperationOutcome::Ready => summary.ready += 1,
                OperationOutcome::Completed => summary.completed += 1,
                OperationOutcome::Unchanged => summary.unchanged += 1,
                outcome if outcome.is_failure() => summary.failed += 1,
                _ => {}
            }
        }
        summary
    }
}

/// Structured data returned by move, copy, hardlink, and symlink commands.
#[derive(Debug, Serialize)]
pub struct ExecutionData {
    /// Filesystem action selected by the command.
    pub action: Action,
    /// Whether this invocation performed read-only test execution.
    pub test: bool,
    /// Aggregate command counts.
    pub summary: ExecutionSummary,
    /// Discovery-ordered execution operations serialized under the stable `items` key.
    #[serde(rename = "items")]
    pub operations: Vec<Operation>,
}

/// Writes human execution output from the same typed result.
pub fn render_execution_human(
    result: &CommandResult<ExecutionData>,
    writer: impl Write,
) -> io::Result<()> {
    render_execution_human_colored(result, writer, false)
}

/// Writes human execution output with optional ANSI outcome colors.
pub fn render_execution_human_colored(
    result: &CommandResult<ExecutionData>,
    mut writer: impl Write,
    color: bool,
) -> io::Result<()> {
    for operation in &result.data.operations {
        let destination = operation
            .destination
            .as_ref()
            .map_or_else(|| "-".into(), |path| path.display().to_string());
        writeln!(
            writer,
            "{:<18} {} -> {}{}",
            styled_outcome(
                operation.outcome,
                result.data.action,
                result.data.test,
                color
            ),
            operation.source.display(),
            destination,
            operation
                .message
                .as_ref()
                .map_or_else(String::new, |message| format!(" ({message})"))
        )?;
    }
    let summary = &result.data.summary;
    writeln!(
        writer,
        "{} discovered, {} ready, {} completed, {} unchanged, {} failed",
        summary.discovered, summary.ready, summary.completed, summary.unchanged, summary.failed
    )?;
    for warning in &result.warnings {
        writeln!(writer, "warning: {warning}")?;
    }
    Ok(())
}

/// Formats a color-aware operation outcome.
fn styled_outcome(outcome: OperationOutcome, action: Action, test: bool, color: bool) -> String {
    let name = outcome_name(outcome, action, test);
    if !color {
        return name;
    }
    let code = match outcome {
        OperationOutcome::Completed => "32",
        OperationOutcome::Ready => "36",
        OperationOutcome::Unchanged => "2",
        OperationOutcome::Skipped => "33",
        OperationOutcome::Unmatched
        | OperationOutcome::Collision
        | OperationOutcome::Exists
        | OperationOutcome::Failed => "31",
    };
    format!("\x1b[{code}m{name}\x1b[0m")
}

/// Returns the action-aware name of an operation outcome.
fn outcome_name(outcome: OperationOutcome, action: Action, test: bool) -> String {
    match outcome {
        OperationOutcome::Ready if test => format!("would {}", action.as_str()),
        OperationOutcome::Ready => "ready".into(),
        OperationOutcome::Completed => action.completed_label().into(),
        OperationOutcome::Unchanged => "unchanged".into(),
        OperationOutcome::Unmatched => "unmatched".into(),
        OperationOutcome::Collision => "collision".into(),
        OperationOutcome::Exists => "exists".into(),
        OperationOutcome::Skipped => "skipped".into(),
        OperationOutcome::Failed => "failed".into(),
    }
}

crate::unit_tests!("output.test.rs");
