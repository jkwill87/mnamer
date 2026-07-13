//! Coordinates media naming, metadata resolution, and filesystem placement.

#![deny(missing_docs)]
#![deny(clippy::missing_docs_in_private_items)]

mod macros;
pub(crate) use macros::unit_tests;
pub mod app;
pub mod cli;
pub mod config;
pub mod execute;
pub mod media;
pub mod net;
