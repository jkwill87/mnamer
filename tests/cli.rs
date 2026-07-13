//! Verifies end-to-end command-line behavior.

use serde_json::Value;
use std::process::Command;

fn binary() -> Command {
    Command::new(env!("CARGO_BIN_EXE_mnamer"))
}

#[test]
fn help_exposes_the_complete_ordered_command_descriptions() {
    let output = binary().arg("help").output().unwrap();
    assert!(output.status.success());
    let stdout = String::from_utf8(output.stdout).unwrap();
    let commands = stdout
        .lines()
        .skip_while(|line| *line != "Commands:")
        .skip(1)
        .take_while(|line| !line.is_empty())
        .map(|line| line.split_whitespace().collect::<Vec<_>>().join(" "))
        .collect::<Vec<_>>();

    #[cfg(not(windows))]
    assert_eq!(
        commands,
        [
            "move Rename media files, moving them to their target locations",
            "copy Rename media files, copying them to their target locations",
            "hardlink Create hard links at target locations, keeping source files in place",
            "symlink Create symbolic links at target locations, keeping source files in place",
            "config Inspect, validate, or initialize `mnamer.toml`",
            "cache Inspect or clear the provider-response cache",
            "provider List or verify metadata providers",
            "help Print this message or the help of the given subcommand(s)",
            "version Display the running mnamer version",
        ]
    );

    #[cfg(windows)]
    assert_eq!(
        commands,
        [
            "move Rename media files, moving them to their target locations",
            "copy Rename media files, copying them to their target locations",
            "config Inspect, validate, or initialize `mnamer.toml`",
            "cache Inspect or clear the provider-response cache",
            "provider List or verify metadata providers",
            "help Print this message or the help of the given subcommand(s)",
            "version Display the running mnamer version",
        ]
    );
}

#[cfg(windows)]
#[test]
fn link_commands_are_rejected_on_windows() {
    for command in ["hardlink", "symlink"] {
        let output = binary().args([command, "movie.mkv"]).output().unwrap();
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
    }
}

#[test]
fn help_is_available_only_as_a_subcommand() {
    let output = binary().args(["help", "copy"]).output().unwrap();
    assert!(output.status.success());
    assert!(
        String::from_utf8(output.stdout)
            .unwrap()
            .contains("Rename media files")
    );

    for args in [vec!["-h"], vec!["--help"], vec!["copy", "-h"]] {
        let output = binary().args(args).output().unwrap();
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
    }
}

#[test]
fn version_is_reported_by_the_version_subcommand() {
    let output = binary().arg("version").output().unwrap();
    assert!(output.status.success());
    assert_eq!(
        String::from_utf8(output.stdout).unwrap(),
        format!("mnamer {}\n", env!("CARGO_PKG_VERSION"))
    );
    assert!(output.stderr.is_empty());

    let output = binary().args(["version", "--json"]).output().unwrap();
    assert!(output.status.success());
    let value: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(value["command"], "version");
    assert_eq!(value["status"], "ok");
    assert_eq!(value["data"]["version"], env!("CARGO_PKG_VERSION"));

    for flag in ["-V", "--version"] {
        let output = binary().arg(flag).output().unwrap();
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stdout.is_empty());
    }
}

#[test]
fn empty_test_execution_emits_one_versioned_json_document() {
    let directory = tempfile::tempdir().unwrap();
    let output = binary()
        .args(["copy", "--test", "--json"])
        .arg(directory.path())
        .output()
        .unwrap();

    assert!(output.status.success());
    assert!(output.stderr.is_empty());
    let value: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(value["schema_version"], 1);
    assert_eq!(value["command"], "copy");
    assert_eq!(value["status"], "empty");
    assert_eq!(value["data"]["action"], "copy");
    assert_eq!(value["data"]["test"], true);
    assert_eq!(value["data"]["summary"]["completed"], 0);
    assert_eq!(
        output.stdout.iter().filter(|byte| **byte == b'\n').count(),
        1
    );
}

#[test]
fn json_configuration_errors_use_stderr_and_exit_two() {
    let directory = tempfile::tempdir().unwrap();
    let missing = directory.path().join("missing.toml");
    let output = binary()
        .arg("--json")
        .arg("--config")
        .arg(missing)
        .args(["config", "show"])
        .output()
        .unwrap();

    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    let value: Value = serde_json::from_slice(&output.stderr).unwrap();
    assert_eq!(value["status"], "error");
    assert_eq!(value["data"]["kind"], "configuration");
}

#[test]
fn config_show_includes_plain_api_keys_in_human_and_json_output() {
    let directory = tempfile::tempdir().unwrap();
    let config = directory.path().join("mnamer.toml");
    std::fs::write(&config, "[api_keys]\ntmdb = \"visible-key\"\n").unwrap();

    let output = binary()
        .arg("--config")
        .arg(&config)
        .args(["config", "show"])
        .output()
        .unwrap();
    assert!(output.status.success());
    assert!(
        String::from_utf8(output.stdout)
            .unwrap()
            .contains("tmdb = \"visible-key\"")
    );

    let output = binary()
        .arg("--json")
        .arg("--config")
        .arg(&config)
        .args(["config", "show"])
        .output()
        .unwrap();
    assert!(output.status.success());
    let value: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(value["data"]["config"]["api_keys"]["tmdb"], "visible-key");
}

#[test]
fn missing_processing_path_is_a_partial_operational_result() {
    let directory = tempfile::tempdir().unwrap();
    let output = binary()
        .args(["--json", "move", "--test", "--batch"])
        .arg(directory.path().join("The.Matrix.1999.mkv"))
        .output()
        .unwrap();

    assert_eq!(output.status.code(), Some(1));
    let value: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(value["status"], "partial");
    assert_eq!(value["data"]["summary"]["failed"], 1);
    assert_eq!(value["data"]["items"][0]["outcome"], "failed");
}

#[test]
fn jobs_without_batch_is_a_cli_error() {
    let directory = tempfile::tempdir().unwrap();

    let output = binary()
        .args(["move", "--jobs", "2"])
        .arg(directory.path())
        .output()
        .unwrap();
    assert_eq!(output.status.code(), Some(2));
    assert!(
        String::from_utf8(output.stderr)
            .unwrap()
            .contains("--jobs requires --batch or --json")
    );
}

#[test]
fn maintenance_commands_honor_global_json_after_subcommands() {
    let output = binary()
        .args(["provider", "list", "--json"])
        .output()
        .unwrap();

    assert!(output.status.success());
    let value: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(value["command"], "provider");
    assert_eq!(value["status"], "ok");
    assert_eq!(value["data"]["providers"].as_array().unwrap().len(), 4);
}

#[test]
fn malformed_typed_ids_are_json_cli_errors() {
    let directory = tempfile::tempdir().unwrap();
    let output = binary()
        .args(["--json", "move", "--batch", "--id", "tmdb:not-a-number"])
        .arg(directory.path())
        .output()
        .unwrap();

    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    let value: Value = serde_json::from_slice(&output.stderr).unwrap();
    assert_eq!(value["data"]["kind"], "usage");
}

#[test]
fn legacy_commands_and_link_overwrite_are_rejected() {
    for args in [
        ["preview", "movie.mkv"].as_slice(),
        ["rename", "movie.mkv"].as_slice(),
        ["hardlink", "movie.mkv", "--overwrite"].as_slice(),
        ["symlink", "movie.mkv", "--overwrite"].as_slice(),
    ] {
        let output = binary().args(args).output().unwrap();
        assert_eq!(
            output.status.code(),
            Some(2),
            "unexpected success for {args:?}"
        );
    }
}
