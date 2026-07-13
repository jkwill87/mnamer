//! Defines normalized metadata candidates returned by providers.

use super::ProviderKind;
use crate::media::Metadata;
use serde::Serialize;

/// A provider result available for selection.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct Candidate {
    /// Provider that returned this result.
    pub provider: ProviderKind,
    /// Normalized provider metadata.
    pub metadata: Metadata,
    /// Provider-specific rank where larger values are better, if available.
    pub score: Option<f64>,
}
