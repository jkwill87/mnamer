//! Defines planned filesystem operations and outcomes.

use crate::media::{MediaKind, Metadata};
use crate::net::provider::ProviderKind;
use serde::Serialize;
use std::fmt;
use std::path::PathBuf;

/// Filesystem action applied to every ready operation in one invocation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Action {
    /// Move each source to its computed destination.
    Move,
    /// Copy each source to its computed destination.
    Copy,
    /// Create a hard link at each computed destination.
    #[cfg(not(windows))]
    Hardlink,
    /// Create a symbolic link at each computed destination.
    #[cfg(not(windows))]
    Symlink,
}

impl Action {
    /// Returns the stable command and JSON name for this action.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Move => "move",
            Self::Copy => "copy",
            #[cfg(not(windows))]
            Self::Hardlink => "hardlink",
            #[cfg(not(windows))]
            Self::Symlink => "symlink",
        }
    }

    /// Returns the completed-action label used by human renderers.
    pub const fn completed_label(self) -> &'static str {
        match self {
            Self::Move => "moved",
            Self::Copy => "copied",
            #[cfg(not(windows))]
            Self::Hardlink => "hardlinked",
            #[cfg(not(windows))]
            Self::Symlink => "symlinked",
        }
    }
}

impl fmt::Display for Action {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.as_str())
    }
}

/// How the final metadata for an execution operation was selected.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MatchOrigin {
    /// A metadata provider result.
    Provider,
    /// Filename-derived metadata accepted as a guess.
    Guess,
}

/// The outcome of planning or applying one execution operation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum OperationOutcome {
    /// The operation is safe and ready to apply.
    Ready,
    /// The selected filesystem action completed successfully.
    Completed,
    /// Source and destination resolve to the same path.
    Unchanged,
    /// No provider result was available.
    Unmatched,
    /// Multiple inputs resolved to the same destination.
    Collision,
    /// The destination already exists.
    Exists,
    /// The target was deliberately skipped.
    Skipped,
    /// Execution failed.
    Failed,
}

impl OperationOutcome {
    /// Returns whether this outcome causes a partial command result.
    pub const fn is_failure(self) -> bool {
        matches!(
            self,
            Self::Unmatched | Self::Collision | Self::Exists | Self::Skipped | Self::Failed
        )
    }
}

/// One source-to-destination operation produced by the planning pipeline.
#[derive(Debug, Clone, Serialize)]
pub struct Operation {
    /// Stable discovery index.
    pub index: usize,
    /// Source path.
    #[serde(serialize_with = "crate::cli::output::path::serialize")]
    pub source: PathBuf,
    /// Computed destination, when available.
    #[serde(serialize_with = "crate::cli::output::path::serialize_option")]
    pub destination: Option<PathBuf>,
    /// Final media category for convenient result inspection.
    pub media_type: MediaKind,
    /// Parsed and enriched metadata.
    pub metadata: Metadata,
    /// Provider selected for this target.
    pub provider: Option<ProviderKind>,
    /// Whether metadata came from a provider or a filename guess.
    pub match_origin: Option<MatchOrigin>,
    /// Current target outcome.
    pub outcome: OperationOutcome,
    /// Human-readable diagnostic for non-ready outcomes.
    pub message: Option<String>,
}

impl Operation {
    /// Creates an initially unresolved execution operation.
    pub const fn unresolved(index: usize, source: PathBuf, metadata: Metadata) -> Self {
        let media_type = metadata.media_type;
        Self {
            index,
            source,
            destination: None,
            media_type,
            metadata,
            provider: None,
            match_origin: None,
            outcome: OperationOutcome::Unmatched,
            message: None,
        }
    }
}

crate::unit_tests!("operation.test.rs");
