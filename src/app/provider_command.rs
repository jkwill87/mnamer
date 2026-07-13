//! Executes metadata-provider maintenance commands.

use super::provider_setup::{CredentialSource, configured_registry};
use super::result::{ApplicationError, ApplicationOutput, generic_ok, operational};
use crate::cli::{Cli, ProviderCommand};
use crate::config::ConfigLoader;
use crate::media::MediaKind;
use crate::net::endpoint::ApiClient;
use crate::net::provider::ProviderKind;
use serde::Serialize;

/// Runs a metadata-provider maintenance command.
pub(super) async fn run(
    cli: &Cli,
    loader: &ConfigLoader,
    command: &ProviderCommand,
) -> Result<ApplicationOutput, ApplicationError> {
    let loaded = loader.load(cli.config.as_deref())?;
    let client = ApiClient::without_cache().map_err(operational)?;
    let (registry, sources) = configured_registry(client, &loaded.config);
    match command {
        ProviderCommand::List => {
            let providers = registry
                .descriptors()
                .into_iter()
                .map(|descriptor| ProviderListEntry {
                    credential_source: sources.get(&descriptor.provider).copied().flatten(),
                    provider: descriptor.provider,
                    media_types: descriptor.media_types,
                    authentication_required: descriptor.authentication_required,
                    configured: descriptor.configured,
                })
                .collect::<Vec<_>>();
            let human = providers
                .iter()
                .map(|provider| {
                    let media = provider
                        .media_types
                        .iter()
                        .map(|media| format!("{media:?}").to_ascii_lowercase())
                        .collect::<Vec<_>>()
                        .join(",");
                    let credential = provider.credential_source.map_or_else(
                        || "none".into(),
                        |source| format!("{source:?}").to_ascii_lowercase(),
                    );
                    format!(
                        "{}: media={media}, auth={}, credential={credential}",
                        provider.provider, provider.authentication_required
                    )
                })
                .collect();
            generic_ok(
                "provider",
                serde_json::to_value(ProviderListData { providers })
                    .map_err(|error| ApplicationError::Operational(error.to_string()))?,
                human,
            )
        }
        ProviderCommand::Check { .. } => {
            let selected = if command.providers().is_empty() {
                ProviderKind::ALL.to_vec()
            } else {
                command.providers().to_vec()
            };
            let mut checks = Vec::with_capacity(selected.len());
            for provider in selected {
                match registry.check(provider).await {
                    Ok(()) => checks.push(ProviderCheckEntry {
                        provider,
                        outcome: ProviderCheckOutcome::Ok,
                        message: None,
                    }),
                    Err(error) => checks.push(ProviderCheckEntry {
                        provider,
                        outcome: ProviderCheckOutcome::Failed,
                        message: Some(error.to_string()),
                    }),
                }
            }
            let failures = checks
                .iter()
                .filter(|check| check.outcome == ProviderCheckOutcome::Failed)
                .count();
            let status = match failures {
                0 => crate::cli::output::CommandStatus::Ok,
                failures if failures == checks.len() => crate::cli::output::CommandStatus::Error,
                _ => crate::cli::output::CommandStatus::Partial,
            };
            let human = checks
                .iter()
                .map(|check| {
                    check.message.as_ref().map_or_else(
                        || format!("{}: ok", check.provider),
                        |message| format!("{}: failed ({message})", check.provider),
                    )
                })
                .collect();
            let result = crate::cli::output::CommandResult::new(
                "provider",
                status,
                serde_json::to_value(ProviderCheckData { checks })
                    .map_err(|error| ApplicationError::Operational(error.to_string()))?,
            );
            Ok(ApplicationOutput::Generic {
                exit_code: result.exit_code(),
                result,
                human,
            })
        }
    }
}

#[derive(Debug, Serialize)]
/// Serializes the complete provider-list result.
struct ProviderListData {
    /// Stores the provider entries.
    providers: Vec<ProviderListEntry>,
}

#[derive(Debug, Serialize)]
/// Serializes one provider-list entry.
struct ProviderListEntry {
    /// Stores the metadata provider.
    provider: ProviderKind,
    /// Stores the supported media categories.
    media_types: Vec<MediaKind>,
    /// Indicates whether the provider requires authentication.
    authentication_required: bool,
    /// Indicates whether the provider has a configured credential.
    configured: bool,
    /// Stores the resolved credential source.
    credential_source: Option<CredentialSource>,
}

#[derive(Debug, Serialize)]
/// Serializes the complete provider-check result.
struct ProviderCheckData {
    /// Stores the provider-check entries.
    checks: Vec<ProviderCheckEntry>,
}

#[derive(Debug, Serialize)]
/// Serializes one provider-check entry.
struct ProviderCheckEntry {
    /// Stores the metadata provider.
    provider: ProviderKind,
    /// Stores the provider-check outcome.
    outcome: ProviderCheckOutcome,
    #[serde(skip_serializing_if = "Option::is_none")]
    /// Stores the diagnostic message.
    message: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
/// Classifies a provider connectivity check.
enum ProviderCheckOutcome {
    /// Marks a successful provider check.
    Ok,
    /// Marks a failed provider check.
    Failed,
}
