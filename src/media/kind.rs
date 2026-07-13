//! Defines supported media categories.

use serde::{Deserialize, Serialize};

/// The media category handled by a target.
#[derive(Debug, Default, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum MediaKind {
    /// A standalone movie.
    Movie,
    /// A television episode.
    Episode,
    /// A filename whose media category could not be inferred.
    #[default]
    Unknown,
}
