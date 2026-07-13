//! Verifies end-to-end subtitle discovery and planning behavior.

use async_trait::async_trait;
use mnamer::app::{ApplicationContext, ApplicationOutput, run_with_context};
use mnamer::cli::Cli;
use mnamer::cli::output::{CommandResult, CommandStatus, render_json};
use mnamer::config::{ConfigLoader, ConfigPaths};
use mnamer::execute::filesystem::{ApplyOptions, apply, preflight};
use mnamer::execute::format::{DestinationFormatter, FormatOptions};
use mnamer::execute::output::{ExecutionData, ExecutionSummary};
use mnamer::execute::plan::{FirstCandidateSelector, Planner, PlanningOptions};
use mnamer::execute::{Action, Operation, OperationOutcome};
use mnamer::media::{MediaKind, Metadata, SubtitleDisposition};
use mnamer::net::provider::{Candidate, CandidateError, CandidateSource, ProviderKind};
use std::ffi::OsString;
use std::fs;
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};

struct FixedSource {
    candidate: Candidate,
    calls: Arc<AtomicUsize>,
}

#[async_trait]
impl CandidateSource for FixedSource {
    async fn search(
        &self,
        _provider: ProviderKind,
        _query: &Metadata,
        _max_results: usize,
    ) -> Result<Vec<Candidate>, CandidateError> {
        self.calls.fetch_add(1, Ordering::Relaxed);
        Ok(vec![self.candidate.clone()])
    }
}

fn movie_candidate(name: &str, year: u16) -> Candidate {
    Candidate {
        provider: ProviderKind::Tmdb,
        metadata: Metadata {
            media_type: MediaKind::Movie,
            name: Some(name.into()),
            year: Some(year),
            id_tmdb: Some("1234".into()),
            ..Metadata::default()
        },
        score: Some(1.0),
    }
}

fn planner(calls: Arc<AtomicUsize>, candidate: Candidate) -> Planner {
    Planner::new(
        Arc::new(FixedSource { candidate, calls }),
        Arc::new(FirstCandidateSelector),
        DestinationFormatter::new(FormatOptions::default()).unwrap(),
        PlanningOptions {
            media: Some(MediaKind::Movie),
            batch: true,
            ..PlanningOptions::default()
        },
    )
}

fn write_sources(directory: &std::path::Path, names: &[&str]) -> Vec<PathBuf> {
    names
        .iter()
        .enumerate()
        .map(|(index, name)| {
            let path = directory.join(name);
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(&path, format!("source-{index}")).unwrap();
            path
        })
        .collect()
}

fn execution_result(
    action: Action,
    test: bool,
    status: CommandStatus,
    items: Vec<Operation>,
) -> CommandResult<ExecutionData> {
    CommandResult::new(
        action.as_str(),
        status,
        ExecutionData {
            action,
            test,
            summary: ExecutionSummary::from_operations(1, &items),
            operations: items,
        },
    )
}

fn execution_cli(
    command: &str,
    test: bool,
    sources: &[PathBuf],
    destination: &std::path::Path,
) -> Cli {
    let mut args = vec![
        OsString::from("mnamer"),
        OsString::from("--json"),
        OsString::from(command),
        OsString::from("--media"),
        OsString::from("movie"),
        OsString::from("--movie-directory"),
        destination.as_os_str().to_owned(),
    ];
    if test {
        args.push(OsString::from("--test"));
    }
    args.extend(sources.iter().map(|path| path.as_os_str().to_owned()));
    Cli::try_parse_validated_from(args).unwrap()
}

#[tokio::test]
async fn every_action_preserves_a_complete_subtitle_bundle() {
    let temporary = tempfile::tempdir().unwrap();
    let media_directory = temporary.path().join("Dune 2 (2024)");
    let names = [
        "Dune 2 (2024).mkv",
        "Dune 2 (2024).en.srt",
        "Subs/English/Forced/track.srt",
        "Dune 2 (2024).en.idx",
        "Dune 2 (2024).en.sub",
    ];
    let sources = write_sources(&media_directory, &names);
    let original_contents = sources
        .iter()
        .map(fs::read_to_string)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    let calls = Arc::new(AtomicUsize::new(0));

    let mut planned = planner(Arc::clone(&calls), movie_candidate("Dune Part Two", 2024))
        .plan(sources.clone())
        .await
        .unwrap()
        .items;
    preflight(
        &mut planned,
        ApplyOptions {
            action: Action::Move,
            overwrite: false,
        },
    );

    assert_eq!(calls.load(Ordering::Relaxed), 1);
    assert!(
        planned
            .iter()
            .all(|item| item.outcome == OperationOutcome::Ready)
    );
    assert!(sources.iter().all(|source| source.exists()));
    assert!(
        planned
            .iter()
            .all(|item| item.destination.as_ref().is_some_and(|path| !path.exists()))
    );
    let forced = planned
        .iter()
        .find(|item| item.source.ends_with("Subs/English/Forced/track.srt"))
        .unwrap();
    assert_eq!(
        forced.metadata.subtitle_dispositions,
        vec![SubtitleDisposition::Forced]
    );
    assert!(
        forced
            .destination
            .as_ref()
            .unwrap()
            .ends_with("Dune Part Two (2024).en.forced.srt")
    );

    let test_result = execution_result(Action::Move, true, CommandStatus::Ok, planned.clone());
    let mut json = Vec::new();
    render_json(&test_result, &mut json).unwrap();
    let document: serde_json::Value = serde_json::from_slice(&json).unwrap();
    assert_eq!(document["status"], "ok");
    assert_eq!(document["command"], "move");
    assert_eq!(document["data"]["action"], "move");
    assert_eq!(document["data"]["test"], true);
    assert_eq!(document["data"]["summary"]["ready"], 5);
    assert!(
        document["data"]["items"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item["metadata"]["subtitle_dispositions"][0] == "forced")
    );

    #[cfg(windows)]
    let actions = [Action::Copy, Action::Move].as_slice();
    #[cfg(not(windows))]
    let actions = [
        Action::Copy,
        Action::Hardlink,
        Action::Symlink,
        Action::Move,
    ]
    .as_slice();

    for &action in actions {
        let mut items = planned.clone();
        for item in &mut items {
            let filename = item.destination.as_ref().unwrap().file_name().unwrap();
            item.destination = Some(temporary.path().join(action.as_str()).join(filename));
        }
        let options = ApplyOptions {
            action,
            overwrite: false,
        };
        preflight(&mut items, options);
        apply(&mut items, options);

        assert!(
            items
                .iter()
                .all(|item| item.outcome == OperationOutcome::Completed)
        );
        for (item, expected) in items.iter().zip(&original_contents) {
            assert_eq!(
                fs::read_to_string(item.destination.as_ref().unwrap()).unwrap(),
                *expected
            );
        }
        assert_eq!(
            sources.iter().all(|source| source.exists()),
            action != Action::Move
        );
    }
}

#[tokio::test]
async fn batch_mode_reports_a_language_less_subtitle_as_partial() {
    let temporary = tempfile::tempdir().unwrap();
    let sources = write_sources(
        temporary.path(),
        &[
            "The.Crow.2024.2160p.WEB.H265-FLAME.mkv",
            "The.Crow.2024.srt",
        ],
    );
    fs::write(&sources[1], b"").unwrap();
    let calls = Arc::new(AtomicUsize::new(0));

    let mut planned = planner(Arc::clone(&calls), movie_candidate("The Crow", 2024))
        .plan(sources)
        .await
        .unwrap()
        .items;
    preflight(
        &mut planned,
        ApplyOptions {
            action: Action::Move,
            overwrite: false,
        },
    );

    assert_eq!(calls.load(Ordering::Relaxed), 1);
    assert_eq!(planned[0].outcome, OperationOutcome::Ready);
    assert_eq!(planned[1].outcome, OperationOutcome::Skipped);
    assert_eq!(
        planned[1].message.as_deref(),
        Some("subtitle language could not be determined")
    );
    let result = execution_result(Action::Move, true, CommandStatus::Partial, planned);
    assert_eq!(result.exit_code(), 1);
    assert_eq!(result.data.summary.ready, 1);
    assert_eq!(result.data.summary.failed, 1);
}

#[tokio::test]
async fn batch_mode_uses_detected_subtitle_content_language() {
    let temporary = tempfile::tempdir().unwrap();
    let sources = write_sources(
        temporary.path(),
        &[
            "The.Crow.2024.2160p.WEB.H265-FLAME.mkv",
            "The.Crow.2024.srt",
        ],
    );
    fs::write(
        &sources[1],
        b"1\n00:00:01,000 --> 00:00:04,000\nThe morning train arrived at the station while everyone waited patiently on the platform.\n",
    )
    .unwrap();
    let calls = Arc::new(AtomicUsize::new(0));

    let planned = planner(Arc::clone(&calls), movie_candidate("The Crow", 2024))
        .plan(sources)
        .await
        .unwrap()
        .items;

    assert_eq!(calls.load(Ordering::Relaxed), 1);
    assert_eq!(planned[0].outcome, OperationOutcome::Ready);
    assert_eq!(planned[1].outcome, OperationOutcome::Ready);
    assert_eq!(planned[1].metadata.language_sub.as_deref(), Some("en"));
    assert!(
        planned[1]
            .destination
            .as_ref()
            .unwrap()
            .ends_with("The Crow (2024).en.srt")
    );
}

#[tokio::test]
async fn application_context_runs_cli_config_discovery_test_and_move_offline() {
    let temporary = tempfile::tempdir().unwrap();
    let media_directory = temporary.path().join("Furiosa (2024)");
    let destination = temporary.path().join("organized");
    fs::write(
        temporary.path().join("mnamer.toml"),
        "[formatting]\nlowercase = true\n",
    )
    .unwrap();
    let sources = write_sources(
        &media_directory,
        &[
            "Furiosa (2024).mkv",
            "Furiosa (2024).en.srt",
            "Subs/English/Forced/track.srt",
            "Furiosa (2024).en.idx",
            "Furiosa (2024).en.sub",
        ],
    );
    let calls = Arc::new(AtomicUsize::new(0));
    let context = ApplicationContext::new(ConfigLoader::new(ConfigPaths::new(
        temporary.path(),
        None,
        Some(temporary.path().join("cache")),
    )))
    .with_candidate_source(Arc::new(FixedSource {
        candidate: movie_candidate("Furiosa A Mad Max Saga", 2024),
        calls: Arc::clone(&calls),
    }));

    #[cfg(windows)]
    let commands = [("move", Action::Move), ("copy", Action::Copy)].as_slice();
    #[cfg(not(windows))]
    let commands = [
        ("move", Action::Move),
        ("copy", Action::Copy),
        ("hardlink", Action::Hardlink),
        ("symlink", Action::Symlink),
    ]
    .as_slice();

    for &(command, action) in commands {
        let tested = run_with_context(
            &execution_cli(command, true, &sources, &destination),
            &context,
        )
        .await
        .unwrap();
        let ApplicationOutput::Execution { result: tested, .. } = tested else {
            panic!("{command} --test returned a maintenance result");
        };
        assert_eq!(tested.status, CommandStatus::Ok);
        assert_eq!(tested.data.action, action);
        assert!(tested.data.test);
        assert_eq!(tested.data.summary.ready, 5);
        assert!(sources.iter().all(|path| path.exists()));
        assert!(!destination.exists());
        assert!(tested.data.operations.iter().all(|item| {
            item.destination
                .as_ref()
                .and_then(|path| path.file_name())
                .is_some_and(|name| name.to_string_lossy() == name.to_string_lossy().to_lowercase())
        }));
    }

    let output = run_with_context(
        &execution_cli("move", false, &sources, &destination),
        &context,
    )
    .await
    .unwrap();
    let ApplicationOutput::Execution { result, .. } = output else {
        panic!("move returned a maintenance result");
    };
    assert_eq!(result.status, CommandStatus::Ok);
    assert_eq!(result.data.summary.completed, 5);
    assert_eq!(calls.load(Ordering::Relaxed), 5);
    assert!(sources.iter().all(|path| !path.exists()));
    assert!(
        result
            .data
            .operations
            .iter()
            .all(|item| item.destination.as_ref().is_some_and(|path| path.exists()))
    );
}
