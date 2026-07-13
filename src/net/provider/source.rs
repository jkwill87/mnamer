//! Defines provider-independent candidate search contracts and failures.

use super::{Candidate, ProviderKind};
use crate::media::Metadata;
use async_trait::async_trait;

/// A provider-independent metadata resolution failure.
#[derive(Debug, thiserror::Error)]
#[error("{message}")]
pub struct CandidateError {
    /// Stores the sanitized error message.
    message: String,
}

impl CandidateError {
    /// Creates a sanitized provider error safe for command output.
    pub fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
        }
    }
}

/// Search interface implemented by the concrete provider registry and test fakes.
#[async_trait]
pub trait CandidateSource: Send + Sync {
    /// Returns provider-ranked normalized candidates for one parsed query.
    async fn search(
        &self,
        provider: ProviderKind,
        query: &Metadata,
        max_results: usize,
    ) -> Result<Vec<Candidate>, CandidateError>;
}
