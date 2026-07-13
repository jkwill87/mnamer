//! Coordinates media grouping, candidate selection, and destination planning.

mod grouping;
mod planner;
mod selection;

pub use planner::{
    Planner, PlanningError, PlanningOptions, PlanningResult, ProviderId, ProviderIdSource,
};
pub use selection::{
    CandidateChoice, CandidateSelector, FirstCandidateSelector, SubtitleLanguageChoice,
};
