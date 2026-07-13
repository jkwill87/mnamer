//! Verifies the intentional pre-1.0 public module layout.

use mediakit::meta::fields::Language;
use mnamer::cli::output::{CommandResult, CommandStatus};
use mnamer::config::ApiKeys;
use mnamer::execute::output::{ExecutionData, ExecutionSummary};
use mnamer::execute::{Action, MatchOrigin, Operation, OperationOutcome};
use mnamer::media::{Metadata, SubtitleFilename};
use mnamer::net::endpoint::ApiClient;
use mnamer::net::provider::{CandidateSource, ProviderKind, ProviderRegistry};
use std::path::Path;
use std::path::PathBuf;

#[test]
fn cohesive_public_paths_are_reachable() {
    let api_keys = ApiKeys {
        tmdb: Some("configured".to_owned()),
        ..ApiKeys::default()
    };
    assert_eq!(api_keys.get(ProviderKind::Tmdb), Some("configured"));
    assert_eq!(api_keys.get(ProviderKind::Tvmaze), None);

    let client = ApiClient::without_cache().unwrap();
    let registry = ProviderRegistry::new(client);
    let _source: &dyn CandidateSource = &registry;
    let mut operation =
        Operation::unresolved(0, PathBuf::from("Apex.2026.mkv"), Metadata::default());
    operation.provider = Some(ProviderKind::Tmdb);
    operation.match_origin = Some(MatchOrigin::Provider);
    operation.outcome = OperationOutcome::Ready;
    let summary = ExecutionSummary::from_operations(1, std::slice::from_ref(&operation));
    let result = CommandResult::new(
        "copy",
        CommandStatus::Ok,
        ExecutionData {
            action: Action::Copy,
            test: true,
            summary,
            operations: vec![operation],
        },
    );

    assert_eq!(result.data.summary.ready, 1);
    let json = serde_json::to_value(&result).unwrap();
    assert!(json["data"].get("items").is_some());
    assert!(json["data"].get("operations").is_none());
    assert_eq!(json["data"]["action"], "copy");
    assert_eq!(json["data"]["test"], true);

    let subtitle = SubtitleFilename::parse(Path::new("Rango.pt-BR.srt")).unwrap();
    let language: Option<Language> = subtitle.language;
    assert_eq!(language.unwrap().iso_639_1, "pt");
}
