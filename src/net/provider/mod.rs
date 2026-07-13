//! Defines provider identities, candidates, registry, and search strategies.

mod candidate;
mod kind;
mod omdb;
mod registry;
mod source;
mod tmdb;
mod tvdb;
mod tvmaze;

pub use candidate::Candidate;
pub use kind::ProviderKind;
pub use registry::{ProviderDescriptor, ProviderError, ProviderRegistry};
pub use source::{CandidateError, CandidateSource};

/// Supplies the embedded TMDb fallback credential.
pub(crate) const EMBEDDED_TMDB_API_KEY: &str = "db972a607f2760bb19ff8bb34074b4c7";
/// Supplies the embedded OMDb fallback credential.
pub(crate) const EMBEDDED_OMDB_API_KEY: &str = "477a7ebc";
/// Supplies the embedded TVDb fallback credential.
pub(crate) const EMBEDDED_TVDB_API_KEY: &str = "E69C7A2CEF2F3152";
