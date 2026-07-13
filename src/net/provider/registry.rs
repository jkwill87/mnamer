//! Dispatches provider searches and manages provider credentials.

use super::{Candidate, CandidateError, CandidateSource, ProviderKind, omdb, tmdb, tvdb, tvmaze};
use crate::media::{MediaKind, Metadata};
use crate::net::endpoint::{self as endpoints, ApiClient, EndpointError};
use async_trait::async_trait;
use serde::Serialize;
use std::collections::HashMap;
use tokio::sync::Mutex;

/// Static capability details for one provider.
#[derive(Debug, Clone, Serialize)]
pub struct ProviderDescriptor {
    /// Provider identifier.
    pub provider: ProviderKind,
    /// Media categories served by the provider.
    pub media_types: Vec<MediaKind>,
    /// Whether live requests require a credential.
    pub authentication_required: bool,
    /// Whether a credential is currently available when required.
    pub configured: bool,
}

/// A high-level provider failure with no credential-bearing context.
#[derive(Debug, thiserror::Error)]
pub enum ProviderError {
    /// The selected provider requires a missing credential.
    #[error("no API key is configured for {0}")]
    MissingCredential(ProviderKind),
    /// A provider identifier was not valid for its endpoint.
    #[error("invalid {provider} identifier {value:?}")]
    InvalidIdentifier {
        /// Provider owning the identifier.
        provider: ProviderKind,
        /// Invalid value.
        value: String,
    },
    /// Parsed metadata lacks fields needed to build a provider query.
    #[error("insufficient metadata for a {0} query")]
    InvalidQuery(ProviderKind),
    /// A language is not accepted by a selected provider API.
    #[error("language {language:?} is not supported by {provider}")]
    UnsupportedLanguage {
        /// Provider rejecting the language.
        provider: ProviderKind,
        /// Requested language identifier.
        language: String,
    },
    /// The asynchronous endpoint layer rejected the request or response.
    #[error(transparent)]
    Endpoint(#[from] EndpointError),
}

/// Shared provider registry backed by one HTTP connection/cache client.
pub struct ProviderRegistry {
    /// Stores the provider API client.
    client: ApiClient,
    /// Stores the provider API keys.
    api_keys: HashMap<ProviderKind, String>,
    /// Stores the cached TVDb authentication token.
    tvdb_token: Mutex<Option<String>>,
}

impl std::fmt::Debug for ProviderRegistry {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter
            .debug_struct("ProviderRegistry")
            .field("client", &"<shared HTTP client>")
            .field("api_keys", &"<redacted>")
            .finish_non_exhaustive()
    }
}

impl ProviderRegistry {
    /// Creates an empty registry. Credentials can be supplied with `with_api_key`.
    pub fn new(client: ApiClient) -> Self {
        Self {
            client,
            api_keys: HashMap::new(),
            tvdb_token: Mutex::new(None),
        }
    }

    /// Adds or replaces a provider credential without exposing it through Debug.
    #[must_use]
    pub fn with_api_key(mut self, provider: ProviderKind, api_key: impl Into<String>) -> Self {
        self.api_keys.insert(provider, api_key.into());
        self
    }

    /// Returns stable provider capability information without making requests.
    pub fn descriptors(&self) -> Vec<ProviderDescriptor> {
        ProviderKind::ALL
            .into_iter()
            .map(|provider| {
                let media_types = match provider {
                    ProviderKind::Tmdb | ProviderKind::Omdb => vec![MediaKind::Movie],
                    ProviderKind::Tvdb | ProviderKind::Tvmaze => vec![MediaKind::Episode],
                };
                let authentication_required = provider.requires_authentication();
                ProviderDescriptor {
                    provider,
                    media_types,
                    authentication_required,
                    configured: !authentication_required || self.api_keys.contains_key(&provider),
                }
            })
            .collect()
    }

    /// Drains non-fatal cache warnings accumulated during provider requests.
    pub fn take_warnings(&self) -> Vec<String> {
        self.client.take_warnings()
    }

    /// Performs the smallest useful live request for one provider.
    pub async fn check(&self, provider: ProviderKind) -> Result<(), ProviderError> {
        match provider {
            ProviderKind::Tmdb => tmdb::check(self).await,
            ProviderKind::Omdb => omdb::check(self).await,
            ProviderKind::Tvdb => tvdb::check(self).await,
            ProviderKind::Tvmaze => tvmaze::check(self).await,
        }
    }

    /// Resolves normalized candidates using the selected provider strategy.
    pub async fn search(
        &self,
        provider: ProviderKind,
        query: &Metadata,
        max_results: usize,
    ) -> Result<Vec<Candidate>, ProviderError> {
        let max_results = max_results.max(1);
        let result = match provider {
            ProviderKind::Tmdb => tmdb::search(self, query, max_results).await,
            ProviderKind::Omdb => omdb::search(self, query, max_results).await,
            ProviderKind::Tvdb => tvdb::search(self, query, max_results).await,
            ProviderKind::Tvmaze => tvmaze::search(self, query, max_results).await,
        };
        match result {
            Err(ProviderError::Endpoint(EndpointError::NotFound { .. })) => Ok(Vec::new()),
            result => result,
        }
    }

    /// Returns the shared API client.
    pub(super) const fn client(&self) -> &ApiClient {
        &self.client
    }

    /// Returns the configured credential for a provider.
    pub(super) fn credential(&self, provider: ProviderKind) -> Result<&str, ProviderError> {
        self.api_keys
            .get(&provider)
            .map(String::as_str)
            .filter(|key| !key.is_empty())
            .ok_or(ProviderError::MissingCredential(provider))
    }

    /// Returns a cached or freshly authenticated TVDb token.
    pub(super) async fn tvdb_token(&self) -> Result<String, ProviderError> {
        let mut token = self.tvdb_token.lock().await;
        if token.is_none() {
            let key = self.credential(ProviderKind::Tvdb)?;
            *token = Some(endpoints::tvdb_v3::tvdb_login(&self.client, key).await?);
        }
        Ok(token.clone().unwrap_or_default())
    }
}

#[async_trait]
impl CandidateSource for ProviderRegistry {
    async fn search(
        &self,
        provider: ProviderKind,
        query: &Metadata,
        max_results: usize,
    ) -> Result<Vec<Candidate>, CandidateError> {
        Self::search(self, provider, query, max_results)
            .await
            .map_err(|error| CandidateError::new(error.to_string()))
    }
}

crate::unit_tests!("registry.test.rs");
