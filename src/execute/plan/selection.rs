//! Defines interactive and deterministic candidate selection.

use crate::media::Metadata;
use crate::net::provider::Candidate;
use mediakit::meta::fields::Language;
use std::path::Path;

/// Result of an interactive match prompt.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CandidateChoice {
    /// Select a candidate by its displayed index.
    Candidate(usize),
    /// Use parsed filename metadata.
    Guess,
    /// Skip this logical target.
    Skip,
    /// Stop processing after the current prompt.
    Quit,
    /// The prompt was interrupted (normally Ctrl-C).
    Interrupted,
}

/// Result of an interactive subtitle-language prompt.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SubtitleLanguageChoice {
    /// Use this validated language.
    Language(Language),
    /// Skip this subtitle only.
    Skip,
    /// Stop processing after the current prompt.
    Quit,
    /// The prompt was interrupted (normally Ctrl-C).
    Interrupted,
}

/// Interactive decisions used by the sequential planning mode.
pub trait CandidateSelector: Send + Sync {
    /// Announces the logical target before provider resolution begins.
    fn processing(&self, _source: &Path, _metadata: &Metadata) {}

    /// Selects a provider candidate, parsed guess, skip, or quit action.
    fn select(
        &self,
        source: &Path,
        candidates: &[Candidate],
        guess: &Metadata,
        allow_guess: bool,
    ) -> CandidateChoice;

    /// Selects a language for a subtitle whose filename has no marker.
    fn subtitle_language(&self, source: &Path) -> SubtitleLanguageChoice;
}

/// A non-interactive selector useful for embedding and tests.
#[derive(Debug, Default)]
pub struct FirstCandidateSelector;

impl CandidateSelector for FirstCandidateSelector {
    fn select(
        &self,
        _source: &Path,
        candidates: &[Candidate],
        _guess: &Metadata,
        allow_guess: bool,
    ) -> CandidateChoice {
        if candidates.is_empty() && allow_guess {
            CandidateChoice::Guess
        } else if candidates.is_empty() {
            CandidateChoice::Skip
        } else {
            CandidateChoice::Candidate(0)
        }
    }

    fn subtitle_language(&self, _source: &Path) -> SubtitleLanguageChoice {
        SubtitleLanguageChoice::Skip
    }
}
