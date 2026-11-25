//! Implements provider HTTP transport, caching, wire types, and endpoints.

mod client;
mod error;
pub mod omdb;
pub mod tmdb;
pub mod tvmaze;
pub mod types;

pub use client::{ApiClient, DEFAULT_CACHE_TTL, build_client, default_cache_path};
pub use error::EndpointError;
