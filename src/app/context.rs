//! Defines injectable application dependencies and system defaults.

use crate::config::{ConfigError, ConfigLoader};
use crate::net::provider::CandidateSource;
use std::sync::Arc;

/// Runtime dependencies used by top-level command orchestration.
///
/// Production callers normally use [`ApplicationContext::system`]. Embedded
/// callers and tests can inject a configuration loader and deterministic
/// candidate source without changing command behavior.
pub struct ApplicationContext {
    /// Stores the configuration loader.
    loader: ConfigLoader,
    /// Stores the injected candidate source.
    candidate_source: Option<Arc<dyn CandidateSource>>,
}

impl ApplicationContext {
    /// Creates a context with an explicitly configured loader.
    pub const fn new(loader: ConfigLoader) -> Self {
        Self {
            loader,
            candidate_source: None,
        }
    }

    /// Creates the production context from process and OS-native locations.
    pub fn system() -> Result<Self, ConfigError> {
        ConfigLoader::system().map(Self::new)
    }

    /// Overrides provider resolution for execution commands.
    #[must_use]
    pub fn with_candidate_source(mut self, source: Arc<dyn CandidateSource>) -> Self {
        self.candidate_source = Some(source);
        self
    }

    /// Returns the configured loader.
    pub(super) const fn loader(&self) -> &ConfigLoader {
        &self.loader
    }

    /// Returns the injected candidate source, if present.
    pub(super) fn candidate_source(&self) -> Option<&Arc<dyn CandidateSource>> {
        self.candidate_source.as_ref()
    }
}
