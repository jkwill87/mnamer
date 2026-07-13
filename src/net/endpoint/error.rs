//! Defines provider HTTP and response-handling failures.

use std::path::PathBuf;

/// Errors returned by media database API endpoint functions.
#[derive(Debug, thiserror::Error)]
pub enum EndpointError {
    /// Invalid parameters, credentials, or another request rejected by a provider.
    #[error("{message}")]
    InvalidRequest {
        /// The error message from the API.
        message: String,
        /// The HTTP status code.
        status: u16,
    },

    /// The requested resource was not found.
    #[error("{message}")]
    NotFound {
        /// The error message from the API.
        message: String,
    },

    /// A network-level error (DNS, timeout, TLS, connection refused).
    ///
    /// The underlying reqwest error is deliberately not retained because it may
    /// contain an authenticated request URL.
    #[error("network request failed: {message}")]
    Network {
        /// A credential-free description of the failure class.
        message: &'static str,
    },

    /// The response body could not be deserialized.
    #[error("response body could not be decoded: {source}")]
    Deserialization {
        /// The JSON decoding error.
        #[source]
        source: serde_json::Error,
    },

    /// The HTTP client could not be constructed.
    #[error("HTTP client initialization failed")]
    ClientInitialization,

    /// The platform-native cache directory could not be determined.
    #[error("the platform-native cache directory is unavailable")]
    CacheDirectoryUnavailable,

    /// A cache maintenance operation failed.
    #[error("failed to {operation} provider cache at {}: {source}", path.display())]
    Cache {
        /// The attempted operation.
        operation: &'static str,
        /// The cache directory.
        path: PathBuf,
        /// The cache backend error.
        #[source]
        source: cacache::Error,
    },
}

impl EndpointError {
    /// Converts a middleware failure into an endpoint error.
    pub(super) fn network(error: &reqwest_middleware::Error) -> Self {
        let message = if error.is_timeout() {
            "request timed out"
        } else if error.is_connect() {
            "could not connect to provider"
        } else if error.is_body() || error.is_decode() {
            "provider response body could not be read"
        } else if error.is_builder() {
            "request could not be constructed"
        } else {
            "provider request could not be completed"
        };
        Self::Network { message }
    }

    /// Converts an HTTP client failure into an endpoint error.
    pub(super) fn reqwest(error: &reqwest::Error) -> Self {
        let message = if error.is_timeout() {
            "request timed out"
        } else if error.is_connect() {
            "could not connect to provider"
        } else if error.is_body() || error.is_decode() {
            "provider response body could not be read"
        } else if error.is_builder() {
            "request could not be constructed"
        } else {
            "provider request could not be completed"
        };
        Self::Network { message }
    }
}

impl From<serde_json::Error> for EndpointError {
    fn from(source: serde_json::Error) -> Self {
        Self::Deserialization { source }
    }
}

crate::unit_tests!("error.test.rs");
