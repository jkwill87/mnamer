//! Orchestrates discovery, metadata resolution, planning, and filesystem execution.

use super::provider_setup::{cache_path, configured_registry};
use super::result::{ApplicationError, ApplicationOutput, operational};
use crate::cli::output::{CommandResult, CommandStatus};
use crate::cli::prompt::{self, CliclackSelector};
use crate::cli::{ExecutionOptions, ExternalIdSource, MediaMode};
use crate::config::ConfigLoader;
use crate::execute::discovery::{DiscoveryOptions, discover};
use crate::execute::filesystem::{ApplyOptions, apply_interruptible, preflight};
use crate::execute::format::{DestinationFormatter, FormatOptions};
use crate::execute::output::{ExecutionData, ExecutionSummary};
use crate::execute::plan::{
    CandidateSelector, FirstCandidateSelector, Planner, PlanningError, PlanningOptions,
    PlanningResult, ProviderId, ProviderIdSource,
};
use crate::execute::{Operation, OperationOutcome};
use crate::media::{MediaKind, Metadata};
use crate::net::endpoint::ApiClient;
use crate::net::provider::CandidateSource;
use mediakit::meta::fields::Language;
use std::io::{self, IsTerminal};
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

/// Runs a media filesystem-action command.
pub(super) async fn run(
    cli: &crate::cli::Cli,
    loader: &ConfigLoader,
    candidate_source_override: Option<&Arc<dyn CandidateSource>>,
) -> Result<ApplicationOutput, ApplicationError> {
    let loaded = loader.load(cli.config.as_deref())?;
    let options = cli
        .execution_options(&loaded.config)
        .expect("execution command has execution options")
        .map_err(|error| ApplicationError::Usage(error.to_string()))?;
    if Language::from_identifier(&options.language).is_none() {
        return Err(ApplicationError::Usage(format!(
            "unsupported language {:?}",
            options.language
        )));
    }

    let discovery = discover(
        &options.paths,
        &DiscoveryOptions {
            recursive: options.recursive,
            extensions: options.extensions.clone(),
            ignore: options.ignore.clone(),
        },
    )
    .map_err(|error| ApplicationError::Usage(error.to_string()))?;
    let discovered_count = discovery.files.len();
    if discovered_count > 0
        && !options.batch
        && (!io::stdin().is_terminal()
            || !io::stdout().is_terminal()
            || !io::stderr().is_terminal())
    {
        return Err(ApplicationError::Usage(
            "interactive processing requires a terminal; pass --batch or --json".into(),
        ));
    }

    let formatter = DestinationFormatter::new(format_options(&options))
        .map_err(|error| ApplicationError::Usage(error.to_string()))?;
    let (candidate_source, registry) = if let Some(source) = candidate_source_override {
        (Arc::clone(source), None)
    } else {
        let client = if options.use_cache {
            ApiClient::new(cache_path(loader)?, loaded.config.cache.ttl(), true)
                .map_err(operational)?
        } else {
            ApiClient::without_cache().map_err(operational)?
        };
        let (registry, _) = configured_registry(client, &loaded.config);
        let registry = Arc::new(registry);
        let candidate_source: Arc<dyn CandidateSource> = registry.clone();
        (candidate_source, Some(registry))
    };
    let command = options.action.as_str();
    let interactive = !options.batch;
    if interactive {
        prompt::begin(options.action, options.test).map_err(operational)?;
    }
    let planning_options = planning_options(&options);
    let selector: Arc<dyn CandidateSelector> = if options.batch {
        Arc::new(FirstCandidateSelector)
    } else {
        Arc::new(CliclackSelector)
    };
    let planner = Planner::new(candidate_source, selector, formatter, planning_options);
    let plan = if discovery.files.is_empty() {
        PlanningResult::default()
    } else {
        tokio::select! {
            result = planner.plan(discovery.files.clone()) => {
                result.map_err(planning_error)?
            }
            signal = tokio::signal::ctrl_c() => {
                signal.map_err(|error| ApplicationError::Operational(error.to_string()))?;
                let items = discovery.files.iter().enumerate().map(|(index, source)| {
                    let mut item = Operation::unresolved(
                        index,
                        source.clone(),
                        Metadata::inspect_with_file_content(
                            source,
                            media_kind(options.media),
                            options.file_inspection,
                        ),
                    );
                    item.outcome = OperationOutcome::Skipped;
                    item.message = Some("interrupted".into());
                    item
                }).collect();
                PlanningResult { items, interrupted: true, quit: false }
            }
        }
    };

    let mut items = plan.items;
    for failure in discovery.failures {
        let mut item = Operation::unresolved(items.len(), failure.path, Metadata::default());
        item.outcome = OperationOutcome::Failed;
        item.message = Some(failure.message);
        items.push(item);
    }
    let apply_options = ApplyOptions {
        action: options.action,
        overwrite: options.overwrite,
    };
    preflight(&mut items, apply_options);

    let mut interrupted = plan.interrupted;
    if !options.test && !interrupted {
        let signal = Arc::new(AtomicBool::new(false));
        let signal_task = {
            let signal = Arc::clone(&signal);
            tokio::spawn(async move {
                if tokio::signal::ctrl_c().await.is_ok() {
                    signal.store(true, Ordering::SeqCst);
                }
            })
        };
        interrupted |=
            apply_interruptible(&mut items, apply_options, || signal.load(Ordering::SeqCst));
        interrupted |= signal.load(Ordering::SeqCst);
        signal_task.abort();
    } else if !options.test && interrupted {
        for item in items
            .iter_mut()
            .filter(|item| item.outcome == OperationOutcome::Ready)
        {
            item.outcome = OperationOutcome::Skipped;
            item.message = Some("interrupted before filesystem write".into());
        }
    }

    let summary = ExecutionSummary::from_operations_with_discovered(
        options.paths.len(),
        discovered_count,
        &items,
    );
    let status = if items.is_empty() {
        CommandStatus::Empty
    } else if summary.failed > 0 {
        CommandStatus::Partial
    } else {
        CommandStatus::Ok
    };
    let mut result = CommandResult::new(
        command,
        status,
        ExecutionData {
            action: options.action,
            test: options.test,
            summary,
            operations: items,
        },
    );
    if let Some(registry) = registry {
        result.warnings = registry.take_warnings();
    }
    let exit_code = if interrupted { 130 } else { result.exit_code() };
    Ok(ApplicationOutput::Execution {
        result,
        exit_code,
        interactive,
    })
}

/// Builds destination-formatting options from resolved execution options.
fn format_options(options: &ExecutionOptions) -> FormatOptions {
    FormatOptions {
        movie_format: options.movie_format.clone(),
        episode_format: options.episode_format.clone(),
        movie_directory: options.movie_directory.as_ref().map(PathBuf::from),
        episode_directory: options.episode_directory.as_ref().map(PathBuf::from),
        lowercase: options.lowercase,
        scene: options.scene,
    }
}

/// Builds planning options from resolved execution options.
fn planning_options(options: &ExecutionOptions) -> PlanningOptions {
    PlanningOptions {
        media: media_kind(options.media),
        file_inspection: options.file_inspection,
        language: Some(options.language.clone()),
        movie_provider: options.movie_provider.into(),
        episode_provider: options.episode_provider.into(),
        max_results: options.max_results,
        allow_guess: options.allow_guess,
        batch: options.batch,
        jobs: usize::from(options.jobs),
        provider_id: options.external_id.as_ref().map(|id| ProviderId {
            source: match id.source {
                ExternalIdSource::Imdb => ProviderIdSource::Imdb,
                ExternalIdSource::Tmdb => ProviderIdSource::Tmdb,
                ExternalIdSource::Tvdb => ProviderIdSource::Tvdb,
                ExternalIdSource::Tvmaze => ProviderIdSource::Tvmaze,
            },
            value: id.value.clone(),
        }),
    }
}

/// Maps a CLI media mode to a concrete media category.
pub(super) const fn media_kind(media: MediaMode) -> Option<MediaKind> {
    match media {
        MediaMode::Auto => None,
        MediaMode::Movie => Some(MediaKind::Movie),
        MediaMode::Episode => Some(MediaKind::Episode),
    }
}

/// Converts a planning failure into an application error.
fn planning_error(error: PlanningError) -> ApplicationError {
    ApplicationError::Usage(error.to_string())
}
