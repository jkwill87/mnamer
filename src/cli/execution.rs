//! Defines filesystem-action arguments and resolved execution options.

use super::values::{parse_extension, parse_glob, parse_positive_usize};
use super::{CliError, ExternalId, MediaMode};
use crate::config::{Config, EpisodeProvider, MovieProvider};
use crate::execute::Action;
use clap::Args;
use std::path::PathBuf;

/// Arguments shared by move, copy, hardlink, and symlink commands.
#[derive(Clone, Debug, Args, PartialEq, Eq)]
pub struct ExecutionArgs {
    /// Files or directories to process.
    #[arg(value_name = "PATH", required = true, num_args = 1..)]
    pub paths: Vec<PathBuf>,

    /// Discover files in subdirectories.
    #[arg(short = 'r', long)]
    pub recursive: bool,

    /// Replace configured extension filters; may be repeated.
    #[arg(
        long = "extension",
        value_name = "EXT",
        action = clap::ArgAction::Append,
        value_parser = parse_extension
    )]
    pub extensions: Vec<String>,

    /// Replace configured case-insensitive glob ignore rules; may be repeated.
    #[arg(
        long = "ignore",
        value_name = "GLOB",
        action = clap::ArgAction::Append,
        value_parser = parse_glob
    )]
    pub ignore: Vec<String>,

    /// Override automatic movie or episode detection.
    #[arg(long, value_enum, default_value_t)]
    pub media: MediaMode,

    /// Select the movie metadata provider.
    #[arg(long, value_enum)]
    pub movie_provider: Option<MovieProvider>,

    /// Select the episode metadata provider.
    #[arg(long, value_enum)]
    pub episode_provider: Option<EpisodeProvider>,

    /// Select the provider result language.
    #[arg(long, value_name = "LANG")]
    pub language: Option<String>,

    /// Limit the number of provider results shown or considered.
    #[arg(long, value_name = "N", value_parser = parse_positive_usize)]
    pub max_results: Option<usize>,

    /// Resolve one logical media item using a typed external ID.
    #[arg(long = "id", value_name = "SOURCE:ID")]
    pub external_id: Option<ExternalId>,

    /// Permit unattended filename-derived fallback after a provider miss.
    #[arg(long)]
    pub allow_guess: bool,

    /// Override the movie filename template.
    #[arg(long, value_name = "TEMPLATE")]
    pub movie_format: Option<String>,

    /// Override the episode filename template.
    #[arg(long, value_name = "TEMPLATE")]
    pub episode_format: Option<String>,

    /// Override the movie destination-directory template.
    #[arg(long, value_name = "TEMPLATE")]
    pub movie_directory: Option<String>,

    /// Override the episode destination-directory template.
    #[arg(long, value_name = "TEMPLATE")]
    pub episode_directory: Option<String>,

    /// Lowercase generated paths.
    #[arg(long)]
    pub lowercase: bool,

    /// Format generated paths using scene conventions.
    #[arg(long)]
    pub scene: bool,

    /// Select the highest-ranked match without prompting.
    #[arg(long)]
    pub batch: bool,

    /// Bound concurrent metadata jobs in batch mode.
    #[arg(long, value_name = "N", value_parser = clap::value_parser!(u8).range(1..=32))]
    pub jobs: Option<u8>,

    /// Resolve and validate operations without modifying files.
    #[arg(long)]
    pub test: bool,

    /// Bypass provider-response cache reads and writes.
    #[arg(long)]
    pub no_cache: bool,

    /// Inspect supported media-container content for technical metadata.
    #[arg(long, conflicts_with = "no_file_inspection")]
    pub file_inspection: bool,

    /// Skip media-container content inspection.
    #[arg(long, conflicts_with = "file_inspection")]
    pub no_file_inspection: bool,
}

impl ExecutionArgs {
    /// Returns whether this invocation uses non-interactive batch selection.
    pub const fn effective_batch(&self, json: bool) -> bool {
        self.batch || json
    }

    /// Validates execution rules that clap cannot express across global options.
    pub const fn validate(&self, json: bool) -> Result<(), CliError> {
        if self.jobs.is_some() && !self.effective_batch(json) {
            return Err(CliError::JobsRequireBatch);
        }
        Ok(())
    }

    /// Resolves the invocation controls and configuration-backed options.
    pub fn resolve(
        &self,
        config: &Config,
        json: bool,
        action: Action,
        overwrite: bool,
    ) -> Result<ExecutionOptions, CliError> {
        self.validate(json)?;

        Ok(ExecutionOptions {
            action,
            test: self.test,
            paths: self.paths.clone(),
            recursive: self.recursive || config.discovery.recursive,
            extensions: if self.extensions.is_empty() {
                config.discovery.extensions.clone()
            } else {
                self.extensions.clone()
            },
            ignore: if self.ignore.is_empty() {
                config.discovery.ignore.clone()
            } else {
                self.ignore.clone()
            },
            media: self.media,
            movie_provider: self.movie_provider.unwrap_or(config.movie.provider),
            episode_provider: self.episode_provider.unwrap_or(config.episode.provider),
            language: self
                .language
                .clone()
                .unwrap_or_else(|| config.matching.language.clone()),
            max_results: self.max_results.unwrap_or(config.matching.max_results),
            external_id: self.external_id.clone(),
            allow_guess: self.allow_guess || config.matching.allow_guess,
            movie_format: self
                .movie_format
                .clone()
                .unwrap_or_else(|| config.movie.format.clone()),
            episode_format: self
                .episode_format
                .clone()
                .unwrap_or_else(|| config.episode.format.clone()),
            movie_directory: self
                .movie_directory
                .clone()
                .or_else(|| config.movie.directory.clone()),
            episode_directory: self
                .episode_directory
                .clone()
                .or_else(|| config.episode.directory.clone()),
            lowercase: self.lowercase || config.formatting.lowercase,
            scene: self.scene || config.formatting.scene,
            batch: self.effective_batch(json),
            jobs: self.jobs.unwrap_or(config.execution.jobs),
            overwrite,
            use_cache: config.cache.enabled && !self.no_cache,
            file_inspection: if self.file_inspection {
                true
            } else if self.no_file_inspection {
                false
            } else {
                config.inspection.file_content
            },
        })
    }
}

/// Fully resolved options for one filesystem execution invocation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExecutionOptions {
    /// Filesystem action selected by the top-level command.
    pub action: Action,
    /// Whether the invocation is strictly non-mutating.
    pub test: bool,
    /// Files or directories to process.
    pub paths: Vec<PathBuf>,
    /// Whether discovery descends into subdirectories.
    pub recursive: bool,
    /// Normalized file extensions eligible for discovery.
    pub extensions: Vec<String>,
    /// Case-insensitive glob ignore rules.
    pub ignore: Vec<String>,
    /// Automatic or forced media classification.
    pub media: MediaMode,
    /// Movie metadata provider.
    pub movie_provider: MovieProvider,
    /// Episode metadata provider.
    pub episode_provider: EpisodeProvider,
    /// Provider result language.
    pub language: String,
    /// Maximum number of provider matches.
    pub max_results: usize,
    /// Optional typed provider or external ID.
    pub external_id: Option<ExternalId>,
    /// Whether filename-derived fallback metadata is permitted.
    pub allow_guess: bool,
    /// Movie filename template.
    pub movie_format: String,
    /// Episode filename template.
    pub episode_format: String,
    /// Optional movie destination-directory template.
    pub movie_directory: Option<String>,
    /// Optional episode destination-directory template.
    pub episode_directory: Option<String>,
    /// Whether generated paths are lowercased.
    pub lowercase: bool,
    /// Whether generated paths use scene conventions.
    pub scene: bool,
    /// Whether provider selection is non-interactive.
    pub batch: bool,
    /// Maximum concurrent provider-resolution jobs.
    pub jobs: u8,
    /// Whether existing destination files may be replaced.
    pub overwrite: bool,
    /// Whether provider-response cache reads and writes are enabled.
    pub use_cache: bool,
    /// Whether supported media-container content is inspected.
    pub file_inspection: bool,
}
