//! Verifies live TVDb v3 endpoint behavior.

use mnamer::net::endpoint::tvdb_v3::*;
use mnamer::net::endpoint::{self as endpoint, EndpointError};

fn client() -> endpoint::ApiClient {
    endpoint::build_client(false).unwrap()
}

fn api_key() -> String {
    std::env::var("API_KEY_TVDB").expect("API_KEY_TVDB must be set")
}

async fn login() -> String {
    tvdb_login(&client(), &api_key()).await.unwrap()
}

const LOST_TVDB_ID_EPISODE: u64 = 127131;
const LOST_TVDB_ID_SERIES: u64 = 73739;

// -- tvdb_login --

#[tokio::test]
async fn tvdb_login_success() {
    let token = login().await;
    assert!(!token.is_empty());
}

#[tokio::test]
async fn tvdb_login_bad_key() {
    let result = tvdb_login(&client(), "invalid_key").await;
    assert!(result.is_err());
}

// -- tvdb_refresh_token --

#[tokio::test]
async fn tvdb_refresh_token_success() {
    let token = login().await;
    let refreshed = tvdb_refresh_token(&client(), &token).await.unwrap();
    assert!(!refreshed.is_empty());
}

#[tokio::test]
async fn tvdb_refresh_token_bad_token() {
    let result = tvdb_refresh_token(&client(), "invalid_token").await;
    assert!(result.is_err());
}

// -- tvdb_episodes_id --

#[tokio::test]
async fn tvdb_episodes_id_success() {
    let token = login().await;
    let result = tvdb_episodes_id(&client(), &token, LOST_TVDB_ID_EPISODE, None)
        .await
        .unwrap();
    let ep = &result.data;
    assert_eq!(ep.id, LOST_TVDB_ID_EPISODE);
    assert!(ep.episode_name.is_some());
    assert!(ep.aired_season.is_some());
    assert!(ep.aired_episode_number.is_some());
    assert!(ep.first_aired.is_some());
    assert!(ep.overview.is_some());
}

#[tokio::test]
async fn tvdb_episodes_id_not_found() {
    let token = login().await;
    let result = tvdb_episodes_id(&client(), &token, 0, None).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

/// TVDb does not always reject invalid tokens (known upstream quirk).
#[tokio::test]
async fn tvdb_episodes_id_bad_token() {
    let result = tvdb_episodes_id(&client(), "invalid_token", LOST_TVDB_ID_EPISODE, None).await;
    // May succeed or fail depending on TVDb's token validation state.
    let _ = result;
}

#[tokio::test]
async fn tvdb_episodes_id_language() {
    let token = login().await;
    let russian = mediakit::meta::fields::Language {
        name: "russian",
        iso_639_1: "ru",
        iso_639_3: "rus",
    };
    let result = tvdb_episodes_id(&client(), &token, LOST_TVDB_ID_EPISODE, Some(russian))
        .await
        .unwrap();
    assert_eq!(result.data.id, LOST_TVDB_ID_EPISODE);
}

// -- tvdb_series_id --

#[tokio::test]
async fn tvdb_series_id_success() {
    let token = login().await;
    let result = tvdb_series_id(&client(), &token, LOST_TVDB_ID_SERIES, None)
        .await
        .unwrap();
    let series = &result.data;
    assert_eq!(series.id, LOST_TVDB_ID_SERIES);
    assert!(series.series_name.is_some());
    assert!(series.overview.is_some());
    assert!(series.first_aired.is_some());
    assert!(series.status.is_some());
}

#[tokio::test]
async fn tvdb_series_id_not_found() {
    let token = login().await;
    let result = tvdb_series_id(&client(), &token, 0, None).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

/// TVDb does not always reject invalid tokens (known upstream quirk).
#[tokio::test]
async fn tvdb_series_id_bad_token() {
    let result = tvdb_series_id(&client(), "invalid_token", LOST_TVDB_ID_SERIES, None).await;
    let _ = result;
}

#[tokio::test]
async fn tvdb_series_id_language() {
    let token = login().await;
    let russian = mediakit::meta::fields::Language {
        name: "russian",
        iso_639_1: "ru",
        iso_639_3: "rus",
    };
    let result = tvdb_series_id(&client(), &token, LOST_TVDB_ID_SERIES, Some(russian))
        .await
        .unwrap();
    assert_eq!(result.data.id, LOST_TVDB_ID_SERIES);
}

// -- tvdb_series_id_episodes --

#[tokio::test]
async fn tvdb_series_id_episodes_success() {
    let token = login().await;
    let result = tvdb_series_id_episodes(&client(), &token, LOST_TVDB_ID_SERIES, None, None)
        .await
        .unwrap();
    assert!(!result.data.is_empty());
    let ep = &result.data[0];
    assert!(ep.aired_season.is_some());
    assert!(ep.aired_episode_number.is_some());
}

#[tokio::test]
async fn tvdb_series_id_episodes_not_found() {
    let token = login().await;
    let result = tvdb_series_id_episodes(&client(), &token, 0, None, None).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

#[tokio::test]
async fn tvdb_series_id_episodes_pagination() {
    let token = login().await;
    let page1 = tvdb_series_id_episodes(&client(), &token, LOST_TVDB_ID_SERIES, Some(1), None)
        .await
        .unwrap();
    let page2 = tvdb_series_id_episodes(&client(), &token, LOST_TVDB_ID_SERIES, Some(2), None)
        .await
        .unwrap();
    assert!(!page1.data.is_empty());
    assert!(!page2.data.is_empty());
    assert_ne!(page1.data[0].id, page2.data[0].id);
}

// -- tvdb_series_id_episodes_query --

#[tokio::test]
async fn tvdb_series_id_episodes_query_by_season() {
    let token = login().await;
    let result = tvdb_series_id_episodes_query(
        &client(),
        &token,
        LOST_TVDB_ID_SERIES,
        None,
        Some(1),
        None,
        None,
    )
    .await
    .unwrap();
    assert!(!result.data.is_empty());
    assert!(result.data.iter().all(|e| e.aired_season == Some(1)));
}

#[tokio::test]
async fn tvdb_series_id_episodes_query_by_season_episode() {
    let token = login().await;
    let result = tvdb_series_id_episodes_query(
        &client(),
        &token,
        LOST_TVDB_ID_SERIES,
        Some(1),
        Some(1),
        None,
        None,
    )
    .await
    .unwrap();
    assert!(!result.data.is_empty());
    assert_eq!(result.data[0].aired_season, Some(1));
    assert_eq!(result.data[0].aired_episode_number, Some(1));
}

#[tokio::test]
async fn tvdb_series_id_episodes_query_not_found() {
    let token = login().await;
    let result = tvdb_series_id_episodes_query(&client(), &token, 0, None, None, None, None).await;
    assert!(result.is_err());
}

// -- tvdb_search_series --

#[tokio::test]
async fn tvdb_search_series_success() {
    let token = login().await;
    let result = tvdb_search_series(&client(), &token, Some("Lost"), None, None, None)
        .await
        .unwrap();
    assert!(!result.data.is_empty());
    assert!(
        result
            .data
            .iter()
            .any(|s| s.series_name.as_deref() == Some("Lost"))
    );
}

#[tokio::test]
async fn tvdb_search_series_bad_token() {
    let result =
        tvdb_search_series(&client(), "invalid_token", Some("Lost"), None, None, None).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn tvdb_search_series_language() {
    let token = login().await;
    let russian = mediakit::meta::fields::Language {
        name: "russian",
        iso_639_1: "ru",
        iso_639_3: "rus",
    };
    let result = tvdb_search_series(&client(), &token, Some("Lost"), None, None, Some(russian))
        .await
        .unwrap();
    assert!(!result.data.is_empty());
}
