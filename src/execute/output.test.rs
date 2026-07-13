//! Verifies execution summaries and human rendering.

use super::*;
use crate::media::Metadata;
use std::path::PathBuf;

#[test]
fn execution_summary_counts_operation_outcomes() {
    let mut operations = [
        (OperationOutcome::Ready, "A.Bugs.Life.1998.mkv"),
        (OperationOutcome::Completed, "Annabelle.Comes.Home.2019.mkv"),
        (OperationOutcome::Failed, "The.Conjuring.2021.mkv"),
    ]
    .into_iter()
    .enumerate()
    .map(|(index, (outcome, source))| {
        let mut operation =
            Operation::unresolved(index, PathBuf::from(source), Metadata::default());
        operation.outcome = outcome;
        operation
    })
    .collect::<Vec<_>>();
    operations.push({
        let mut operation = Operation::unresolved(
            3,
            PathBuf::from("Kingdom.of.the.Planet.of.the.Apes.2024.mkv"),
            Metadata::default(),
        );
        operation.outcome = OperationOutcome::Unchanged;
        operation
    });

    let summary = ExecutionSummary::from_operations(4, &operations);

    assert_eq!(summary.ready, 1);
    assert_eq!(summary.completed, 1);
    assert_eq!(summary.unchanged, 1);
    assert_eq!(summary.failed, 1);
}

#[test]
fn human_output_uses_action_specific_test_language() {
    let mut operation = Operation::unresolved(
        0,
        PathBuf::from("A.Bugs.Life.1998.mkv"),
        Metadata::default(),
    );
    operation.destination = Some(PathBuf::from("A Bug's Life (1998).mkv"));
    operation.outcome = OperationOutcome::Ready;
    let result = CommandResult::new(
        "copy",
        crate::cli::output::CommandStatus::Ok,
        ExecutionData {
            action: Action::Copy,
            test: true,
            summary: ExecutionSummary::from_operations(1, std::slice::from_ref(&operation)),
            operations: vec![operation],
        },
    );
    let mut output = Vec::new();

    render_execution_human(&result, &mut output).unwrap();

    let output = String::from_utf8(output).unwrap();
    assert!(output.contains("would copy"));
    assert!(output.contains("0 completed"));
}
