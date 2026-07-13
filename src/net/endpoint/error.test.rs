//! Verifies provider HTTP error behavior.

use super::*;

#[test]
fn display_invalid_request() {
    let err = EndpointError::InvalidRequest {
        message: "invalid API key".into(),
        status: 401,
    };
    assert_eq!(err.to_string(), "invalid API key");
}

#[test]
fn display_not_found() {
    let err = EndpointError::NotFound {
        message: "Movie not found!".into(),
    };
    assert_eq!(err.to_string(), "Movie not found!");
}
