//! Verifies provider HTTP transport and response caching.

use std::time::Duration;

use serde_json::json;
use tempfile::TempDir;
use wiremock::matchers::{method, path};
use wiremock::{Mock, MockServer, ResponseTemplate};

use super::*;

fn cache_key() -> SemanticCacheKey {
    SemanticCacheKey::new("test", "fixture").parameter("id", 42)
}

async fn mount_json(server: &MockServer, expected_calls: u64) {
    Mock::given(method("GET"))
        .and(path("/fixture"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({"id": 42})))
        .expect(expected_calls)
        .mount(server)
        .await;
}

#[tokio::test]
async fn successful_get_is_reused_from_cache() {
    let server = MockServer::start().await;
    mount_json(&server, 1).await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::from_secs(60), true).unwrap();
    let url = format!("{}/fixture", server.uri());

    let first = client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();
    let second = client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();

    assert_eq!(
        first.json::<serde_json::Value>().unwrap(),
        json!({"id": 42})
    );
    assert_eq!(
        second.json::<serde_json::Value>().unwrap(),
        json!({"id": 42})
    );
}

#[tokio::test]
async fn bypass_disables_cache_reads_and_writes() {
    let server = MockServer::start().await;
    mount_json(&server, 2).await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::from_secs(60), true).unwrap();
    let bypassed = client.bypass_cache();
    let url = format!("{}/fixture", server.uri());

    client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();
    bypassed
        .send_get(bypassed.get(&url), &cache_key())
        .await
        .unwrap();
}

#[tokio::test]
async fn expired_entry_is_fetched_again() {
    let server = MockServer::start().await;
    mount_json(&server, 2).await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::ZERO, true).unwrap();
    let url = format!("{}/fixture", server.uri());

    client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();
    client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();
}

#[tokio::test]
async fn corrupt_entry_is_evicted_and_refetched() {
    let server = MockServer::start().await;
    mount_json(&server, 1).await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::from_secs(60), true).unwrap();
    let key = cache_key();
    cacache::write(cache.path(), key.canonical(), b"not json")
        .await
        .unwrap();

    let response = client
        .send_get(client.get(format!("{}/fixture", server.uri())), &key)
        .await
        .unwrap();

    assert_eq!(
        response.json::<serde_json::Value>().unwrap(),
        json!({"id": 42})
    );
}

#[tokio::test]
async fn ordinary_cache_failure_falls_back_to_network() {
    let server = MockServer::start().await;
    mount_json(&server, 1).await;
    let invalid_cache_directory = tempfile::NamedTempFile::new().unwrap();
    let client = ApiClient::new(
        invalid_cache_directory.path(),
        Duration::from_secs(60),
        true,
    )
    .unwrap();

    let response = client
        .send_get(
            client.get(format!("{}/fixture", server.uri())),
            &cache_key(),
        )
        .await
        .unwrap();

    assert_eq!(
        response.json::<serde_json::Value>().unwrap(),
        json!({"id": 42})
    );
    assert!(!client.take_warnings().is_empty());
}

#[tokio::test]
async fn request_errors_do_not_expose_authenticated_urls() {
    let client = ApiClient::without_cache().unwrap();
    let result = client
        .send_get(
            client.get("://invalid.example/?api_key=super-secret"),
            &cache_key(),
        )
        .await;
    let Err(error) = result else {
        panic!("invalid URL unexpectedly produced a response");
    };

    let diagnostic = format!("{error:?} {error}");
    assert!(!diagnostic.contains("super-secret"));
    assert!(!diagnostic.contains("api_key"));
}

#[tokio::test]
async fn unsuccessful_response_is_not_cached() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/fixture"))
        .respond_with(ResponseTemplate::new(404).set_body_json(json!({"error": "missing"})))
        .expect(2)
        .mount(&server)
        .await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::from_secs(60), true).unwrap();
    let url = format!("{}/fixture", server.uri());

    for _ in 0..2 {
        let response = client
            .send_get(client.get(&url), &cache_key())
            .await
            .unwrap();
        assert_eq!(response.status, StatusCode::NOT_FOUND);
    }
}

#[tokio::test]
async fn application_level_error_is_not_cached() {
    let server = MockServer::start().await;
    mount_json(&server, 2).await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::from_secs(60), true).unwrap();
    let url = format!("{}/fixture", server.uri());

    for _ in 0..2 {
        client
            .send_get_validated(client.get(&url), &cache_key(), |_| false)
            .await
            .unwrap();
    }
}

#[tokio::test]
async fn transient_failure_is_retried_at_most_three_times() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/fixture"))
        .respond_with(ResponseTemplate::new(503).set_body_json(json!({"error": "busy"})))
        .expect(4)
        .mount(&server)
        .await;
    let client = ApiClient::without_cache().unwrap();

    let response = client
        .send_get(
            client.get(format!("{}/fixture", server.uri())),
            &cache_key(),
        )
        .await
        .unwrap();

    assert_eq!(response.status, StatusCode::SERVICE_UNAVAILABLE);
}

#[tokio::test]
async fn retry_after_beyond_bound_is_not_retried_early() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/fixture"))
        .respond_with(
            ResponseTemplate::new(429)
                .insert_header("Retry-After", "60")
                .set_body_json(json!({"error": "slow down"})),
        )
        .expect(1)
        .mount(&server)
        .await;
    let client = ApiClient::without_cache().unwrap();

    let response = client
        .send_get(
            client.get(format!("{}/fixture", server.uri())),
            &cache_key(),
        )
        .await
        .unwrap();

    assert_eq!(response.status, StatusCode::TOO_MANY_REQUESTS);
}

#[test]
fn retry_after_supports_delta_seconds_and_http_dates() {
    let now = SystemTime::now();
    let delta = HeaderValue::from_static("3");
    assert_eq!(parse_retry_after(&delta, now), Some(Duration::from_secs(3)));

    let retry_at = now + Duration::from_secs(2);
    let date = HeaderValue::from_str(&httpdate::fmt_http_date(retry_at)).unwrap();
    let delay = parse_retry_after(&date, now).unwrap();
    assert!(delay <= Duration::from_secs(2));
    assert!(delay >= Duration::from_secs(1));
}

#[tokio::test]
async fn clear_removes_cached_responses() {
    let server = MockServer::start().await;
    mount_json(&server, 2).await;
    let cache = TempDir::new().unwrap();
    let client = ApiClient::new(cache.path(), Duration::from_secs(60), true).unwrap();
    let url = format!("{}/fixture", server.uri());

    client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();
    client.clear_cache().await.unwrap();
    client
        .send_get(client.get(&url), &cache_key())
        .await
        .unwrap();
}

#[tokio::test]
async fn clear_reports_cache_maintenance_failure() {
    let invalid_cache_directory = tempfile::NamedTempFile::new().unwrap();
    let client = ApiClient::new(
        invalid_cache_directory.path(),
        Duration::from_secs(60),
        true,
    )
    .unwrap();

    let error = client.clear_cache().await;

    assert!(matches!(error, Err(EndpointError::Cache { .. })));
}

#[test]
fn semantic_cache_key_is_sorted_and_contains_no_implicit_credentials() {
    let first = SemanticCacheKey::new("provider", "search")
        .parameter("title", "Arrival")
        .parameter("year", 2016)
        .parameter("api_key", "super-secret");
    let second = SemanticCacheKey::new("provider", "search")
        .parameter("year", 2016)
        .parameter("title", "Arrival");

    assert_eq!(first.canonical(), second.canonical());
    assert!(!first.canonical().contains("api_key"));
    assert!(!first.canonical().contains("token"));
    assert!(!first.canonical().contains("super-secret"));
}
