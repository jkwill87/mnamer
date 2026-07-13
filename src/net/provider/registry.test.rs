//! Verifies provider registration, credentials, and dispatch.

use super::*;

#[test]
fn descriptors_report_media_and_authentication() {
    let registry = ProviderRegistry::new(ApiClient::without_cache().unwrap());

    let descriptors = registry.descriptors();

    assert_eq!(descriptors.len(), 4);
    assert!(
        descriptors
            .iter()
            .find(|item| item.provider == ProviderKind::Tvmaze)
            .is_some_and(|item| !item.authentication_required && item.configured)
    );
    assert!(
        descriptors
            .iter()
            .find(|item| item.provider == ProviderKind::Tmdb)
            .is_some_and(|item| item.authentication_required && !item.configured)
    );
}

#[test]
fn debug_never_contains_credentials() {
    let registry = ProviderRegistry::new(ApiClient::without_cache().unwrap())
        .with_api_key(ProviderKind::Tmdb, "top-secret");

    assert!(!format!("{registry:?}").contains("top-secret"));
}

#[tokio::test]
async fn tvmaze_external_lookup_requires_exactly_one_identifier() {
    let client = ApiClient::without_cache().unwrap();

    let neither = endpoints::tvmaze::tvmaze_show_lookup(&client, None, None).await;
    let both = endpoints::tvmaze::tvmaze_show_lookup(&client, Some("tt1"), Some(1)).await;

    assert!(matches!(neither, Err(EndpointError::InvalidRequest { .. })));
    assert!(matches!(both, Err(EndpointError::InvalidRequest { .. })));
}
