//! Organizes provider-specific wire response models.

pub mod omdb;
pub mod tmdb;
pub mod tvdb_v3;
pub mod tvmaze;

crate::unit_tests!("../types.test.rs");
