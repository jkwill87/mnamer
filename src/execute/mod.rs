//! Coordinates discovery, planning, formatting, and filesystem actions.

pub mod discovery;
pub mod filesystem;
pub mod format;
mod operation;
pub mod output;
pub mod plan;

pub use operation::{Action, MatchOrigin, Operation, OperationOutcome};
