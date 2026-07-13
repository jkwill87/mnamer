//! Implements retrying HTTP transport and response caching.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use directories::ProjectDirs;
use http::Extensions;
use reqwest::header::{HeaderValue, RETRY_AFTER};
use reqwest::{Request, Response, StatusCode};
use reqwest_middleware::{
    ClientBuilder, ClientWithMiddleware, Middleware, Next, RequestBuilder,
    Result as MiddlewareResult,
};
use reqwest_retry::{
    Jitter, RetryDecision, RetryPolicy, Retryable, default_on_request_failure,
    default_on_request_success, policies::ExponentialBackoff,
};
use serde::de::DeserializeOwned;

use super::error::EndpointError;

/// Versions the serialized response-cache schema.
const CACHE_SCHEMA_VERSION: u8 = 1;
/// Bounds one provider HTTP request.
const DEFAULT_REQUEST_TIMEOUT: Duration = Duration::from_secs(30);
/// Limits provider HTTP retry attempts.
const MAX_RETRIES: u32 = 3;
/// Bounds the delay before a provider retry.
const MAX_RETRY_DELAY: Duration = Duration::from_secs(4);

/// The default lifetime of a successful provider response in the local cache.
pub const DEFAULT_CACHE_TTL: Duration = Duration::from_secs(6 * 24 * 60 * 60);

/// Returns the platform-native provider response cache directory.
pub fn default_cache_path() -> Result<PathBuf, EndpointError> {
    ProjectDirs::from("", "", "mnamer")
        .map(|dirs| dirs.cache_dir().join("provider-responses"))
        .ok_or(EndpointError::CacheDirectoryUnavailable)
}

/// Builds an API client using the platform-native cache path and default TTL.
pub fn build_client(cache_enabled: bool) -> Result<ApiClient, EndpointError> {
    ApiClient::new(default_cache_path()?, DEFAULT_CACHE_TTL, cache_enabled)
}

/// Shared asynchronous HTTP client for media provider endpoints.
///
/// A client owns one connection pool and retry stack. Clone it freely; clones
/// continue to share the underlying pool. Credentials are supplied only to
/// individual endpoint calls and are never retained by this type.
#[derive(Clone)]
pub struct ApiClient {
    /// Stores the middleware-enabled HTTP client.
    inner: ClientWithMiddleware,
    /// Stores the optional response cache.
    cache: Option<ResponseCache>,
    /// Indicates whether the response caching is enabled.
    cache_enabled: bool,
    /// Stores the non-fatal cache warnings.
    warnings: Arc<Mutex<Vec<String>>>,
}

impl ApiClient {
    /// Creates a client with an explicit cache directory, TTL, and enabled state.
    pub fn new(
        cache_path: impl Into<PathBuf>,
        cache_ttl: Duration,
        cache_enabled: bool,
    ) -> Result<Self, EndpointError> {
        Self::build(
            Some(ResponseCache {
                path: cache_path.into(),
                ttl: cache_ttl,
            }),
            cache_enabled,
        )
    }

    /// Creates a client which never reads or writes the provider cache.
    pub fn without_cache() -> Result<Self, EndpointError> {
        Self::build(None, false)
    }

    /// Builds an API client with optional response caching.
    fn build(cache: Option<ResponseCache>, cache_enabled: bool) -> Result<Self, EndpointError> {
        let transport = reqwest::Client::builder()
            .timeout(DEFAULT_REQUEST_TIMEOUT)
            .user_agent(concat!("mnamer/", env!("CARGO_PKG_VERSION")))
            .build()
            .map_err(|_| EndpointError::ClientInitialization)?;
        let retry_policy = ExponentialBackoff::builder()
            .retry_bounds(Duration::from_millis(250), MAX_RETRY_DELAY)
            .jitter(Jitter::Bounded)
            .build_with_max_retries(MAX_RETRIES);
        let inner = ClientBuilder::new(transport)
            .with(BoundedRetryMiddleware { retry_policy })
            .build();
        Ok(Self {
            inner,
            cache,
            cache_enabled,
            warnings: Arc::new(Mutex::new(Vec::new())),
        })
    }

    /// Returns a clone which bypasses cache reads and writes.
    #[must_use]
    pub fn bypass_cache(&self) -> Self {
        let mut client = self.clone();
        client.cache_enabled = false;
        client
    }

    /// Returns the configured cache directory, if this client has one.
    #[must_use]
    pub fn cache_path(&self) -> Option<&Path> {
        self.cache.as_ref().map(|cache| cache.path.as_path())
    }

    /// Drains non-fatal cache diagnostics accumulated by this client and its clones.
    pub fn take_warnings(&self) -> Vec<String> {
        let mut warnings = self
            .warnings
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        std::mem::take(&mut *warnings)
    }

    /// Removes all provider response cache entries.
    ///
    /// Unlike ordinary cache reads and writes, a maintenance failure is
    /// returned to the caller.
    pub async fn clear_cache(&self) -> Result<(), EndpointError> {
        let Some(cache) = &self.cache else {
            return Err(EndpointError::CacheDirectoryUnavailable);
        };
        if !cache.path.exists() {
            return Ok(());
        }
        cacache::clear(&cache.path)
            .await
            .map_err(|source| EndpointError::Cache {
                operation: "clear",
                path: cache.path.clone(),
                source,
            })
    }

    /// Creates an HTTP GET request builder.
    pub(super) fn get(&self, url: impl reqwest::IntoUrl) -> RequestBuilder {
        self.inner.get(url)
    }

    /// Creates an HTTP POST request builder.
    pub(super) fn post(&self, url: impl reqwest::IntoUrl) -> RequestBuilder {
        self.inner.post(url)
    }

    /// Sends a cache-aware GET request.
    pub(super) async fn send_get(
        &self,
        request: RequestBuilder,
        key: &SemanticCacheKey,
    ) -> Result<ApiResponse, EndpointError> {
        self.send_get_validated(request, key, is_json).await
    }

    /// Sends and validates a cache-aware GET request.
    pub(super) async fn send_get_validated(
        &self,
        request: RequestBuilder,
        key: &SemanticCacheKey,
        cacheable: fn(&[u8]) -> bool,
    ) -> Result<ApiResponse, EndpointError> {
        if self.cache_enabled
            && let Some(body) = self.read_cache(key, cacheable).await
        {
            return Ok(ApiResponse {
                status: StatusCode::OK,
                body,
            });
        }

        let response = self.send_uncached(request).await?;
        if self.cache_enabled && response.status.is_success() && cacheable(&response.body) {
            self.write_cache(key, &response.body).await;
        }
        Ok(response)
    }

    /// Sends a request without response caching.
    pub(super) async fn send_uncached(
        &self,
        request: RequestBuilder,
    ) -> Result<ApiResponse, EndpointError> {
        let response = request
            .send()
            .await
            .map_err(|error| EndpointError::network(&error))?;
        let status = response.status();
        let body = response
            .bytes()
            .await
            .map_err(|error| EndpointError::reqwest(&error))?
            .to_vec();
        Ok(ApiResponse { status, body })
    }

    /// Reads a validated response from the cache.
    async fn read_cache(
        &self,
        key: &SemanticCacheKey,
        cacheable: fn(&[u8]) -> bool,
    ) -> Option<Vec<u8>> {
        let cache = self.cache.as_ref()?;
        let key = key.canonical();
        let metadata = match cacache::metadata(&cache.path, &key).await {
            Ok(Some(metadata)) => metadata,
            Ok(None) => return None,
            Err(_) => {
                self.warn_cache("read metadata", &cache.path);
                self.remove_cache_entry(&key).await;
                return None;
            }
        };

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis();
        if now.saturating_sub(metadata.time) >= cache.ttl.as_millis() {
            self.remove_cache_entry(&key).await;
            return None;
        }

        match cacache::read(&cache.path, &key).await {
            Ok(body) if cacheable(&body) => Some(body),
            Ok(_) => {
                self.remove_cache_entry(&key).await;
                None
            }
            Err(_) => {
                self.warn_cache("read", &cache.path);
                self.remove_cache_entry(&key).await;
                None
            }
        }
    }

    /// Writes a response to the cache.
    async fn write_cache(&self, key: &SemanticCacheKey, body: &[u8]) {
        let Some(cache) = &self.cache else {
            return;
        };
        if cacache::write(&cache.path, key.canonical(), body)
            .await
            .is_err()
        {
            self.warn_cache("write", &cache.path);
        }
    }

    /// Removes one response-cache entry.
    async fn remove_cache_entry(&self, key: &str) {
        let Some(cache) = &self.cache else {
            return;
        };
        if cacache::remove(&cache.path, key).await.is_err() {
            self.warn_cache("evict", &cache.path);
        }
    }

    /// Records a non-fatal response-cache warning.
    fn warn_cache(&self, operation: &'static str, path: &Path) {
        let warning = format!(
            "provider cache {operation} failed at {}; continuing without cache",
            path.display()
        );
        tracing::warn!(operation, cache_path = %path.display(), "{warning}");
        let mut warnings = self
            .warnings
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        if !warnings.contains(&warning) {
            warnings.push(warning);
        }
    }
}

/// Applies a bounded retry policy to HTTP requests.
struct BoundedRetryMiddleware {
    /// Stores the bounded retry policy.
    retry_policy: ExponentialBackoff,
}

#[async_trait::async_trait]
impl Middleware for BoundedRetryMiddleware {
    async fn handle(
        &self,
        request: Request,
        extensions: &mut Extensions,
        next: Next<'_>,
    ) -> MiddlewareResult<Response> {
        let started_at = SystemTime::now();
        let mut retries = 0;

        loop {
            let Some(attempt) = request.try_clone() else {
                // Requests with streaming bodies cannot be replayed safely.
                return next.run(request, extensions).await;
            };
            let result = next.clone().run(attempt, extensions).await;
            let retryable = match &result {
                Ok(response) => default_on_request_success(response),
                Err(error) => default_on_request_failure(error),
            };
            if retryable != Some(Retryable::Transient) {
                return result;
            }

            let RetryDecision::Retry { execute_after } =
                self.retry_policy.should_retry(started_at, retries)
            else {
                return result;
            };
            let policy_delay = execute_after
                .duration_since(SystemTime::now())
                .unwrap_or_default();
            let server_delay = result
                .as_ref()
                .ok()
                .and_then(|response| response.headers().get(RETRY_AFTER))
                .and_then(|value| parse_retry_after(value, SystemTime::now()));
            if server_delay.is_some_and(|delay| delay > MAX_RETRY_DELAY) {
                // A bounded client must not sleep indefinitely, and retrying
                // before the provider's requested time would violate the hint.
                return result;
            }
            let delay = server_delay.map_or(policy_delay, |delay| delay.max(policy_delay));
            tracing::debug!(
                retry = retries + 1,
                ?delay,
                "retrying transient provider request"
            );
            tokio::time::sleep(delay).await;
            retries += 1;
        }
    }
}

/// Parses an HTTP retry delay.
fn parse_retry_after(value: &HeaderValue, now: SystemTime) -> Option<Duration> {
    let value = value.to_str().ok()?.trim();
    if let Ok(seconds) = value.parse::<u64>() {
        return Some(Duration::from_secs(seconds));
    }
    httpdate::parse_http_date(value)
        .ok()
        .map(|retry_at| retry_at.duration_since(now).unwrap_or_default())
}

#[derive(Clone)]
/// Configures response-cache storage and expiration.
struct ResponseCache {
    /// Stores the response-cache path.
    path: PathBuf,
    /// Stores the response-cache lifetime.
    ttl: Duration,
}

/// Stores an HTTP response status and body.
pub(super) struct ApiResponse {
    /// Stores the HTTP status code.
    pub(super) status: StatusCode,
    /// Stores the response body.
    body: Vec<u8>,
}

impl ApiResponse {
    /// Deserializes the response body as JSON.
    pub(super) fn json<T: DeserializeOwned>(&self) -> Result<T, EndpointError> {
        Ok(serde_json::from_slice(&self.body)?)
    }

    /// Decodes the response body as text.
    pub(super) fn text(&self) -> String {
        String::from_utf8_lossy(&self.body).into_owned()
    }
}

/// Builds credential-free keys for cached provider requests.
pub(super) struct SemanticCacheKey {
    /// Stores the metadata provider.
    provider: &'static str,
    /// Stores the provider endpoint name.
    endpoint: &'static str,
    /// Stores the canonical request parameters.
    parameters: BTreeMap<&'static str, String>,
}

impl SemanticCacheKey {
    /// Creates an empty semantic cache key.
    pub(super) const fn new(provider: &'static str, endpoint: &'static str) -> Self {
        Self {
            provider,
            endpoint,
            parameters: BTreeMap::new(),
        }
    }

    /// Adds a required cache-key parameter.
    pub(super) fn parameter(mut self, name: &'static str, value: impl ToString) -> Self {
        if is_secret_parameter(name) {
            tracing::error!("refused to include a credential in a provider cache key");
            return self;
        }
        self.parameters.insert(name, value.to_string());
        self
    }

    /// Adds an optional cache-key parameter.
    pub(super) fn optional<T: ToString>(mut self, name: &'static str, value: Option<T>) -> Self {
        if let Some(value) = value {
            self = self.parameter(name, value);
        }
        self
    }

    /// Renders the canonical credential-free cache key.
    fn canonical(&self) -> String {
        let mut key = format!(
            "v{CACHE_SCHEMA_VERSION}|p{}:{}|e{}:{}",
            self.provider.len(),
            self.provider,
            self.endpoint.len(),
            self.endpoint
        );
        for (name, value) in &self.parameters {
            key.push_str(&format!(
                "|{}:{}={}:{}",
                name.len(),
                name,
                value.len(),
                value
            ));
        }
        key
    }
}

/// Returns whether a response body begins with JSON.
fn is_json(body: &[u8]) -> bool {
    serde_json::from_slice::<serde_json::Value>(body).is_ok()
}

/// Returns whether a parameter name identifies a credential.
fn is_secret_parameter(name: &str) -> bool {
    matches!(
        name.to_ascii_lowercase().as_str(),
        "api_key" | "apikey" | "authorization" | "bearer" | "token" | "access_token"
    )
}

crate::unit_tests!("client.test.rs");
