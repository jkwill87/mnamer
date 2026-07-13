//! Resolves metadata candidates and plans destination operations.

use super::grouping::{LogicalTarget, ParsedItem, group_subtitles};
use super::selection::{CandidateChoice, CandidateSelector, SubtitleLanguageChoice};
use crate::execute::format::{DestinationFormatter, FormatError};
use crate::execute::{MatchOrigin, Operation, OperationOutcome};
use crate::media::subtitle::normalize_association_text;
use crate::media::{MediaFormat, MediaKind, Metadata, SubtitleDisposition, SubtitleFilename};
use crate::net::provider::{CandidateSource, ProviderKind};
use futures_util::{StreamExt, stream};
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

/// A typed provider-specific identifier supplied for one logical target.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProviderId {
    /// Namespace owning the identifier.
    pub source: ProviderIdSource,
    /// Provider-specific ID value.
    pub value: String,
}

/// Namespaces accepted by the typed `--id` option.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProviderIdSource {
    /// IMDb title ID, resolved through the configured media provider.
    Imdb,
    /// TMDb movie ID.
    Tmdb,
    /// TVDb series ID.
    Tvdb,
    /// TVmaze show ID.
    Tvmaze,
}

/// Options controlling metadata resolution and match selection.
#[derive(Debug, Clone)]
pub struct PlanningOptions {
    /// Explicit media hint passed into `mediakit` inspection.
    pub media: Option<MediaKind>,
    /// Whether supported media-container content is inspected.
    pub file_inspection: bool,
    /// Provider response/search language.
    pub language: Option<String>,
    /// Movie metadata provider.
    pub movie_provider: ProviderKind,
    /// Episode metadata provider.
    pub episode_provider: ProviderKind,
    /// Maximum candidates requested from a provider.
    pub max_results: usize,
    /// Permit parsed metadata when a provider does not produce a match.
    pub allow_guess: bool,
    /// Automatically select the highest-ranked candidate.
    pub batch: bool,
    /// Maximum concurrent provider resolutions in batch mode.
    pub jobs: usize,
    /// Optional provider ID for the sole logical target.
    pub provider_id: Option<ProviderId>,
}

impl Default for PlanningOptions {
    fn default() -> Self {
        Self {
            media: None,
            file_inspection: true,
            language: None,
            movie_provider: ProviderKind::Tmdb,
            episode_provider: ProviderKind::Tvmaze,
            max_results: 5,
            allow_guess: false,
            batch: false,
            jobs: 4,
            provider_id: None,
        }
    }
}

/// Planning result including terminal-control state.
#[derive(Debug, Default)]
pub struct PlanningResult {
    /// Discovery-ordered execution operations.
    pub items: Vec<Operation>,
    /// Whether processing was interrupted and should exit 130.
    pub interrupted: bool,
    /// Whether the user chose to quit normally.
    pub quit: bool,
}

/// A fatal planning configuration error.
#[derive(Debug, thiserror::Error)]
pub enum PlanningError {
    /// A typed ID can only unambiguously address one video plus its subtitles.
    #[error("--id requires exactly one logical media target")]
    ProviderIdRequiresSingleTarget,
    /// A provider ID does not support the parsed or selected media kind.
    #[error("provider {provider} does not support {media:?} media")]
    ProviderMediaMismatch {
        /// Provider selected by the typed ID.
        provider: ProviderKind,
        /// Parsed or selected media type.
        media: MediaKind,
    },
    /// A destination template could not be rendered.
    #[error(transparent)]
    Format(#[from] FormatError),
}

/// Resolves provider metadata and computes pure source/destination operations.
pub struct Planner {
    /// Stores the candidate source.
    source: Arc<dyn CandidateSource>,
    /// Stores the candidate selector.
    selector: Arc<dyn CandidateSelector>,
    /// Stores the destination formatter.
    formatter: DestinationFormatter,
    /// Stores the resolved options.
    options: PlanningOptions,
}

impl Planner {
    /// Creates a planner with injected provider and interaction implementations.
    pub fn new(
        source: Arc<dyn CandidateSource>,
        selector: Arc<dyn CandidateSelector>,
        formatter: DestinationFormatter,
        options: PlanningOptions,
    ) -> Self {
        Self {
            source,
            selector,
            formatter,
            options,
        }
    }

    /// Plans all discovered files without mutating the filesystem.
    pub async fn plan(&self, files: Vec<PathBuf>) -> Result<PlanningResult, PlanningError> {
        let parsed = files
            .into_iter()
            .enumerate()
            .map(|(index, source)| {
                let mut metadata = Metadata::inspect_with_file_content(
                    &source,
                    self.options.media,
                    self.options.file_inspection,
                );
                if let Some(language) = &self.options.language {
                    metadata.language = Some(language.clone());
                }
                ParsedItem {
                    index,
                    source,
                    metadata,
                }
            })
            .collect::<Vec<_>>();
        let groups = group_subtitles(&parsed);
        if self.options.provider_id.is_some() && groups.len() != 1 {
            return Err(PlanningError::ProviderIdRequiresSingleTarget);
        }

        let mut result = if self.options.batch {
            let jobs = self.options.jobs.clamp(1, 32);
            let parsed = &parsed;
            let mut resolved = stream::iter(
                groups
                    .into_iter()
                    .map(|group| async move { self.resolve_group(group, parsed, false).await }),
            )
            .buffer_unordered(jobs)
            .collect::<Vec<_>>()
            .await
            .into_iter()
            .collect::<Result<Vec<_>, _>>()?;
            resolved.sort_by_key(|resolved| resolved.order);
            PlanningResult {
                items: resolved
                    .into_iter()
                    .flat_map(|resolved| resolved.items)
                    .collect(),
                ..PlanningResult::default()
            }
        } else {
            let mut result = PlanningResult::default();
            for (position, group) in groups.iter().cloned().enumerate() {
                let resolved = self.resolve_group(group, &parsed, true).await?;
                result.items.extend(resolved.items);
                if resolved.interrupted || resolved.quit {
                    result.interrupted = resolved.interrupted;
                    result.quit = resolved.quit;
                    for remaining in groups.iter().skip(position + 1) {
                        result.items.extend(skipped_group(
                            remaining,
                            &parsed,
                            "not processed after quit",
                        ));
                    }
                    break;
                }
            }
            result
        };
        result.items.sort_by_key(|item| item.index);
        Ok(result)
    }

    /// Resolves provider metadata for one logical target.
    async fn resolve_group(
        &self,
        group: LogicalTarget,
        parsed: &[ParsedItem],
        interactive: bool,
    ) -> Result<GroupResult, PlanningError> {
        let primary = &parsed[group.primary];
        if interactive {
            self.selector.processing(&primary.source, &primary.metadata);
        }
        let mut query = primary.metadata.clone();
        let provider = if let Some(provider_id) = &self.options.provider_id {
            apply_provider_id(&mut query, provider_id);
            let provider = match provider_id.source {
                ProviderIdSource::Imdb => match query.media_type {
                    MediaKind::Movie => self.options.movie_provider,
                    MediaKind::Episode => self.options.episode_provider,
                    MediaKind::Unknown => self.options.movie_provider,
                },
                ProviderIdSource::Tmdb => ProviderKind::Tmdb,
                ProviderIdSource::Tvdb => ProviderKind::Tvdb,
                ProviderIdSource::Tvmaze => ProviderKind::Tvmaze,
            };
            if query.media_type != MediaKind::Unknown && !provider.supports(query.media_type) {
                return Err(PlanningError::ProviderMediaMismatch {
                    provider,
                    media: query.media_type,
                });
            }
            provider
        } else {
            match query.media_type {
                MediaKind::Movie => self.options.movie_provider,
                MediaKind::Episode => self.options.episode_provider,
                MediaKind::Unknown => {
                    return Ok(self.guess_or_fail_group(
                        group,
                        parsed,
                        "media type could not be determined",
                    ));
                }
            }
        };

        let candidates = self
            .source
            .search(provider, &query, self.options.max_results)
            .await;
        let (selection, provider_message) = match candidates {
            Ok(candidates) => {
                let selection = if interactive {
                    let offer_guess = guess_is_usable(&query)
                        && (self.options.allow_guess || candidates.is_empty());
                    self.selector
                        .select(&primary.source, &candidates, &query, offer_guess)
                } else if candidates.is_empty() && self.options.allow_guess {
                    CandidateChoice::Guess
                } else if candidates.is_empty() {
                    CandidateChoice::Skip
                } else {
                    CandidateChoice::Candidate(0)
                };
                ((candidates, selection), None)
            }
            Err(error) => {
                return Ok(group_with_provider(
                    failed_group(
                        group,
                        parsed,
                        OperationOutcome::Failed,
                        format!("{provider}: {error}"),
                    ),
                    provider,
                ));
            }
        };
        let (candidates, choice) = selection;
        match choice {
            CandidateChoice::Candidate(index) => {
                let Some(candidate) = candidates.get(index) else {
                    return Ok(group_with_provider(
                        failed_group(
                            group,
                            parsed,
                            OperationOutcome::Failed,
                            "selected candidate is unavailable".into(),
                        ),
                        provider,
                    ));
                };
                self.finish_group(
                    group,
                    parsed,
                    &candidate.metadata,
                    Some(candidate.provider),
                    MatchOrigin::Provider,
                    provider_message,
                    interactive,
                )
            }
            CandidateChoice::Guess if guess_is_usable(&query) => self.finish_group(
                group,
                parsed,
                &query,
                Some(provider),
                MatchOrigin::Guess,
                provider_message,
                interactive,
            ),
            CandidateChoice::Guess => Ok(group_with_provider(
                failed_group(
                    group,
                    parsed,
                    OperationOutcome::Unmatched,
                    "filename metadata is insufficient for a safe guess".into(),
                ),
                provider,
            )),
            CandidateChoice::Skip => Ok(group_with_provider(
                failed_group(
                    group,
                    parsed,
                    if candidates.is_empty() {
                        OperationOutcome::Unmatched
                    } else {
                        OperationOutcome::Skipped
                    },
                    if candidates.is_empty() {
                        "provider returned no matches".into()
                    } else {
                        "skipped by user".into()
                    },
                ),
                provider,
            )),
            CandidateChoice::Quit => Ok(GroupResult {
                order: group.order,
                items: skipped_group(&group, parsed, "not processed after quit"),
                quit: true,
                interrupted: false,
            }),
            CandidateChoice::Interrupted => Ok(GroupResult {
                order: group.order,
                items: skipped_group(&group, parsed, "interrupted"),
                quit: false,
                interrupted: true,
            }),
        }
    }

    /// Falls back to parsed metadata or fails one logical target.
    fn guess_or_fail_group(
        &self,
        group: LogicalTarget,
        parsed: &[ParsedItem],
        message: &str,
    ) -> GroupResult {
        if self.options.allow_guess && guess_is_usable(&parsed[group.primary].metadata) {
            self.finish_group(
                group.clone(),
                parsed,
                &parsed[group.primary].metadata,
                None,
                MatchOrigin::Guess,
                Some(message.into()),
                false,
            )
            .unwrap_or_else(|error| {
                failed_group(group, parsed, OperationOutcome::Failed, error.to_string())
            })
        } else {
            failed_group(group, parsed, OperationOutcome::Unmatched, message.into())
        }
    }

    #[expect(
        clippy::too_many_arguments,
        reason = "group completion keeps the resolution context explicit"
    )]
    /// Formats destinations and operations for one resolved group.
    fn finish_group(
        &self,
        group: LogicalTarget,
        parsed: &[ParsedItem],
        selected: &Metadata,
        provider: Option<ProviderKind>,
        origin: MatchOrigin,
        message: Option<String>,
        interactive: bool,
    ) -> Result<GroupResult, PlanningError> {
        let mut items = Vec::with_capacity(group.members.len());
        let mut companion_language_choices = HashMap::new();
        let mut quit = false;
        let mut interrupted = false;
        for &member in &group.members {
            let parsed_item = &parsed[member];
            let mut metadata = parsed_item.metadata.clone();
            metadata.overlay(selected);
            let mut item =
                Operation::unresolved(parsed_item.index, parsed_item.source.clone(), metadata);
            item.provider = provider;
            item.match_origin = Some(origin);
            item.message.clone_from(&message);

            if quit || interrupted {
                item.outcome = OperationOutcome::Skipped;
                item.message = Some(if interrupted {
                    "interrupted".into()
                } else {
                    "not processed after quit".into()
                });
                items.push(item);
                continue;
            }

            if item.metadata.is_subtitle() && item.metadata.language_sub.is_none() {
                let companion_key = subtitle_companion_key(&item.source);
                let choice = companion_key
                    .as_ref()
                    .and_then(|key| companion_language_choices.get(key).cloned())
                    .unwrap_or_else(|| {
                        let choice = if interactive {
                            self.selector.subtitle_language(&item.source)
                        } else {
                            SubtitleLanguageChoice::Skip
                        };
                        if let Some(key) = companion_key {
                            companion_language_choices.insert(key, choice.clone());
                        }
                        choice
                    });
                match choice {
                    SubtitleLanguageChoice::Language(language) => {
                        item.metadata.language_sub = Some(language.iso_639_1.to_owned());
                    }
                    SubtitleLanguageChoice::Skip => {
                        item.outcome = OperationOutcome::Skipped;
                        item.message = Some("subtitle language could not be determined".into());
                        items.push(item);
                        continue;
                    }
                    SubtitleLanguageChoice::Quit => {
                        item.outcome = OperationOutcome::Skipped;
                        item.message = Some("not processed after quit".into());
                        quit = true;
                        items.push(item);
                        continue;
                    }
                    SubtitleLanguageChoice::Interrupted => {
                        item.outcome = OperationOutcome::Skipped;
                        item.message = Some("interrupted".into());
                        interrupted = true;
                        items.push(item);
                        continue;
                    }
                }
            }

            match self.formatter.destination(&item.source, &item.metadata) {
                Ok(destination) => {
                    item.destination = Some(destination);
                    item.outcome = OperationOutcome::Ready;
                }
                Err(error) => {
                    item.outcome = OperationOutcome::Failed;
                    item.message = Some(error.to_string());
                }
            }
            items.push(item);
        }
        Ok(GroupResult {
            order: group.order,
            items,
            quit,
            interrupted,
        })
    }
}

#[derive(Debug)]
/// Collects planned operations for one logical target.
struct GroupResult {
    /// Stores the logical-target order.
    order: usize,
    /// Stores the planned operations.
    items: Vec<Operation>,
    /// Indicates whether the interactive selection requested termination.
    quit: bool,
    /// Indicates whether the planning was interrupted.
    interrupted: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
/// Identifies companion subtitle files.
struct SubtitleCompanionKey {
    /// Stores the subtitle directory.
    directory: PathBuf,
    /// Stores the normalized subtitle stem.
    stem: String,
    /// Stores the subtitle dispositions.
    dispositions: Vec<SubtitleDisposition>,
}

/// Builds a stable key for companion subtitle files.
fn subtitle_companion_key(path: &Path) -> Option<SubtitleCompanionKey> {
    let subtitle = SubtitleFilename::parse(path)?;
    if !matches!(subtitle.format, MediaFormat::Idx | MediaFormat::Sub) {
        return None;
    }
    let stem = path
        .file_stem()
        .and_then(|value| value.to_str())
        .map(normalize_association_text)
        .filter(|value| !value.is_empty())?;
    Some(SubtitleCompanionKey {
        directory: path.parent().unwrap_or_else(|| Path::new("")).to_path_buf(),
        stem,
        dispositions: subtitle.dispositions,
    })
}

/// Applies an explicit provider identifier to a metadata query.
fn apply_provider_id(query: &mut Metadata, provider_id: &ProviderId) {
    match provider_id.source {
        ProviderIdSource::Imdb => query.id_imdb = Some(provider_id.value.clone()),
        ProviderIdSource::Tmdb => query.id_tmdb = Some(provider_id.value.clone()),
        ProviderIdSource::Tvdb => query.id_tvdb = Some(provider_id.value.clone()),
        ProviderIdSource::Tvmaze => query.id_tvmaze = Some(provider_id.value.clone()),
    }
}

/// Returns whether parsed metadata can support destination planning.
fn guess_is_usable(metadata: &Metadata) -> bool {
    match metadata.media_type {
        MediaKind::Movie => metadata
            .name
            .as_deref()
            .is_some_and(|name| !name.is_empty()),
        MediaKind::Episode => {
            metadata
                .series
                .as_deref()
                .is_some_and(|series| !series.is_empty())
                && (metadata.date.is_some()
                    || (metadata.season.is_some() && metadata.episode.is_some()))
        }
        MediaKind::Unknown => false,
    }
}

/// Creates failed operations for a logical target.
fn failed_group(
    group: LogicalTarget,
    parsed: &[ParsedItem],
    outcome: OperationOutcome,
    message: String,
) -> GroupResult {
    GroupResult {
        order: group.order,
        items: group
            .members
            .into_iter()
            .map(|member| {
                let parsed = &parsed[member];
                let mut item = Operation::unresolved(
                    parsed.index,
                    parsed.source.clone(),
                    parsed.metadata.clone(),
                );
                item.outcome = outcome;
                item.message = Some(message.clone());
                item
            })
            .collect(),
        quit: false,
        interrupted: false,
    }
}

/// Annotates planned operations with the selected provider.
fn group_with_provider(mut group: GroupResult, provider: ProviderKind) -> GroupResult {
    for item in &mut group.items {
        item.provider = Some(provider);
    }
    group
}

/// Creates skipped operations for a logical target.
fn skipped_group(group: &LogicalTarget, parsed: &[ParsedItem], message: &str) -> Vec<Operation> {
    group
        .members
        .iter()
        .map(|&member| {
            let parsed = &parsed[member];
            let mut item =
                Operation::unresolved(parsed.index, parsed.source.clone(), parsed.metadata.clone());
            item.outcome = OperationOutcome::Skipped;
            item.message = Some(message.into());
            item
        })
        .collect()
}

crate::unit_tests!("planner.test.rs");
