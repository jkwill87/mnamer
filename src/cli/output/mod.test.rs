//! Verifies typed command outcomes and JSON rendering.

use super::*;
use serde_json::json;

#[test]
fn json_envelope_is_versioned_and_compact() {
    let result = CommandResult::new(
        "cache.path",
        CommandStatus::Ok,
        json!({"path": "/tmp/cache"}),
    );
    let mut output = Vec::new();

    render_json(&result, &mut output).unwrap();

    let value: serde_json::Value = serde_json::from_slice(&output).unwrap();
    assert_eq!(value["schema_version"], 1);
    assert_eq!(value["command"], "cache.path");
    assert_eq!(value["status"], "ok");
    assert_eq!(output.iter().filter(|byte| **byte == b'\n').count(), 1);
}

#[test]
fn status_exit_codes_follow_the_public_contract() {
    assert_eq!(CommandStatus::Ok.exit_code(), 0);
    assert_eq!(CommandStatus::Empty.exit_code(), 0);
    assert_eq!(CommandStatus::Partial.exit_code(), 1);
    assert_eq!(CommandStatus::Error.exit_code(), 1);
}
