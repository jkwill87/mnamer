//! Implements interactive terminal prompts with `cliclack`.

use crate::cli::output::CommandResult;
use crate::execute::output::ExecutionData;
use crate::execute::plan::{CandidateChoice, CandidateSelector, SubtitleLanguageChoice};
use crate::execute::{Action, Operation, OperationOutcome};
use crate::media::{MediaKind, Metadata};
use crate::net::provider::Candidate;
use cliclack::{Theme, ThemeState};
use console::Style;
use mediakit::meta::fields::LANG_ALL;
use std::io::{self, IsTerminal};
use std::path::Path;

/// Configures the mnamer theme and announces an interactive execution run.
pub fn begin(action: Action, test: bool) -> io::Result<()> {
    configure_theme();
    if test {
        cliclack::log::warning(format!(
            "Test mode — no files will be modified; planned action: {action}"
        ))?;
    }
    cliclack::log::step("Starting mnamer")
}

/// Renders the completed interactive execution result as cliclack event nodes.
pub fn render_result(result: &CommandResult<ExecutionData>) -> io::Result<()> {
    for operation in &result.data.operations {
        match operation.outcome {
            OperationOutcome::Ready => {
                if let Some(destination) = &operation.destination {
                    cliclack::log::success(format!(
                        "Would {} to {}",
                        result.data.action,
                        destination.display()
                    ))?;
                }
            }
            OperationOutcome::Completed => {
                if let Some(destination) = &operation.destination {
                    cliclack::log::success(format!(
                        "{} to {}",
                        completed_sentence_label(result.data.action),
                        destination.display()
                    ))?;
                }
            }
            OperationOutcome::Unchanged => {
                cliclack::log::info(format!("Already in place: {}", operation.source.display()))?;
            }
            OperationOutcome::Skipped | OperationOutcome::Unmatched => {
                cliclack::log::warning(operation_message(operation))?;
            }
            OperationOutcome::Collision | OperationOutcome::Exists | OperationOutcome::Failed => {
                cliclack::log::error(operation_message(operation))?;
            }
        }
    }
    for warning in &result.warnings {
        cliclack::log::warning(warning)?;
    }

    let summary = &result.data.summary;
    let successful = summary.ready + summary.completed + summary.unchanged;
    let message = format!(
        "{successful} out of {} files processed successfully",
        summary.discovered
    );
    if successful == 0 && summary.failed > 0 {
        cliclack::outro_cancel(message)
    } else {
        cliclack::outro(message)
    }
}

/// Interactive selector for sequential execution commands.
#[derive(Debug, Default)]
pub struct CliclackSelector;

impl CandidateSelector for CliclackSelector {
    fn processing(&self, source: &Path, metadata: &Metadata) {
        let _ = cliclack::log::step(processing_label(source, metadata));
    }

    fn select(
        &self,
        _source: &Path,
        candidates: &[Candidate],
        guess: &Metadata,
        allow_guess: bool,
    ) -> CandidateChoice {
        let mut choices = candidates
            .iter()
            .enumerate()
            .map(|(index, candidate)| {
                (
                    MatchChoice::Candidate(index),
                    candidate_label(candidate),
                    candidate.provider.to_string(),
                )
            })
            .collect::<Vec<_>>();
        if allow_guess {
            choices.push((
                MatchChoice::Guess,
                guess_label(guess),
                "use filename metadata".into(),
            ));
        }
        choices.push((
            MatchChoice::Skip,
            "Skip this target".into(),
            "continue with the next target".into(),
        ));
        choices.push((
            MatchChoice::Quit,
            "Quit".into(),
            "stop after this prompt".into(),
        ));
        match cliclack::select("Select match")
            .items(&choices)
            .max_rows(choices.len().clamp(4, 12))
            .interact()
        {
            Ok(MatchChoice::Candidate(index)) => CandidateChoice::Candidate(index),
            Ok(MatchChoice::Guess) => CandidateChoice::Guess,
            Ok(MatchChoice::Skip) => CandidateChoice::Skip,
            Ok(MatchChoice::Quit) => CandidateChoice::Quit,
            Err(_) => CandidateChoice::Interrupted,
        }
    }

    fn subtitle_language(&self, _source: &Path) -> SubtitleLanguageChoice {
        let mut choices = LANG_ALL
            .into_iter()
            .copied()
            .map(|language| {
                (
                    LanguageChoice::Language(language),
                    language.name,
                    language.iso_639_1,
                )
            })
            .collect::<Vec<_>>();
        choices.push((
            LanguageChoice::Skip,
            "Skip this subtitle",
            "leave its language unresolved",
        ));
        choices.push((LanguageChoice::Quit, "Quit", "stop after this prompt"));
        match cliclack::select("Select language")
            .items(&choices)
            .max_rows(12)
            .filter_mode()
            .interact()
        {
            Ok(LanguageChoice::Language(language)) => SubtitleLanguageChoice::Language(language),
            Ok(LanguageChoice::Skip) => SubtitleLanguageChoice::Skip,
            Ok(LanguageChoice::Quit) => SubtitleLanguageChoice::Quit,
            Err(_) => SubtitleLanguageChoice::Interrupted,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
/// Represents an interactive metadata-match choice.
enum MatchChoice {
    /// Selects a provider candidate by position.
    Candidate(usize),
    /// Selects parsed filename metadata.
    Guess,
    /// Skips the current media target.
    Skip,
    /// Stops interactive selection.
    Quit,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
/// Represents an interactive subtitle-language choice.
enum LanguageChoice {
    /// Selects a concrete subtitle language.
    Language(mediakit::meta::fields::Language),
    /// Skips the current subtitle.
    Skip,
    /// Stops interactive selection.
    Quit,
}

/// Formats a candidate-selection label.
fn candidate_label(candidate: &Candidate) -> String {
    metadata_label(&candidate.metadata)
}

/// Formats a concise media metadata label.
fn metadata_label(metadata: &Metadata) -> String {
    let suffix = match metadata.media_type {
        MediaKind::Movie => metadata
            .year
            .map_or_else(String::new, |year| format!(" ({year})")),
        MediaKind::Episode => match (metadata.season, metadata.episode) {
            (Some(season), Some(episode)) => format!(" S{season:02}E{episode:02}"),
            _ => metadata
                .date
                .as_ref()
                .map_or_else(String::new, |date| format!(" {date}")),
        },
        MediaKind::Unknown => String::new(),
    };
    let episode_title = if metadata.media_type == MediaKind::Episode {
        metadata
            .title
            .as_ref()
            .map_or_else(String::new, |title| format!(" - {title}"))
    } else {
        String::new()
    };
    format!("{}{}{}", metadata.display_name(), suffix, episode_title)
}

/// Formats a parsed-metadata guess label.
fn guess_label(metadata: &Metadata) -> String {
    format!("Use filename guess: {}", metadata_label(metadata))
}

/// Formats the label shown while processing a source.
fn processing_label(source: &Path, metadata: &Metadata) -> String {
    let media_type = match metadata.media_type {
        MediaKind::Movie => "Movie",
        MediaKind::Episode => "Episode",
        MediaKind::Unknown => "Media",
    };
    let description = if metadata.is_subtitle() {
        format!("{media_type} Subtitle")
    } else {
        media_type.into()
    };
    let filename = source.file_name().map_or_else(
        || source.display().to_string(),
        |name| name.to_string_lossy().into(),
    );
    let size = metadata
        .file_size
        .map_or_else(|| "unknown size".into(), human_file_size);
    format!("Processing {description} \"{filename}\" ({size})")
}

/// Formats a byte count for terminal display.
fn human_file_size(bytes: u64) -> String {
    const UNITS: [&str; 5] = ["B", "KB", "MB", "GB", "TB"];
    let mut size = bytes as f64;
    for (index, unit) in UNITS.iter().enumerate() {
        if size < 1024.0 || index == UNITS.len() - 1 {
            return format!("{size:.2}{unit}");
        }
        size /= 1024.0;
    }
    unreachable!("the final unit always returns")
}

/// Formats the in-progress message for an operation.
fn operation_message(operation: &Operation) -> String {
    operation.message.as_ref().map_or_else(
        || format!("Could not process {}", operation.source.display()),
        |message| format!("{}: {message}", operation.source.display()),
    )
}

/// Returns the completed-action sentence label.
const fn completed_sentence_label(action: Action) -> &'static str {
    match action {
        Action::Move => "Moved",
        Action::Copy => "Copied",
        #[cfg(not(windows))]
        Action::Hardlink => "Hardlinked",
        #[cfg(not(windows))]
        Action::Symlink => "Symlinked",
    }
}

/// Configures terminal prompt colors.
fn configure_theme() {
    console::set_colors_enabled_stderr(io::stderr().is_terminal());
    cliclack::set_theme(MnamerTheme);
}

/// Defines the terminal prompt theme.
struct MnamerTheme;

impl Theme for MnamerTheme {
    fn bar_color(&self, state: &ThemeState) -> Style {
        match state {
            ThemeState::Active => Style::new().magenta(),
            ThemeState::Cancel => Style::new().red(),
            ThemeState::Submit => Style::new().cyan().dim(),
            ThemeState::Error(_) => Style::new().yellow(),
        }
    }

    fn state_symbol_color(&self, state: &ThemeState) -> Style {
        match state {
            ThemeState::Active => Style::new().magenta(),
            ThemeState::Submit => Style::new().green(),
            ThemeState::Cancel => Style::new().red(),
            ThemeState::Error(_) => Style::new().yellow(),
        }
    }

    fn info_symbol(&self) -> String {
        Style::new().blue().apply_to("●").to_string()
    }

    fn warning_symbol(&self) -> String {
        Style::new().yellow().apply_to("▲").to_string()
    }

    fn error_symbol(&self) -> String {
        Style::new().red().apply_to("■").to_string()
    }

    fn active_symbol(&self) -> String {
        Style::new().green().apply_to("◆").to_string()
    }

    fn submit_symbol(&self) -> String {
        Style::new().cyan().apply_to("◇").to_string()
    }
}

crate::unit_tests!("prompt.test.rs");
