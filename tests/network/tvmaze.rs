//! Verifies live TVmaze endpoint behavior.

use mnamer::net::endpoint::tvmaze::*;
use mnamer::net::endpoint::{self as endpoint, EndpointError};

fn client() -> endpoint::ApiClient {
    endpoint::build_client(false).unwrap()
}

// -- tvmaze_show --

#[tokio::test]
async fn tvmaze_show_success() {
    let show = tvmaze_show(&client(), 73, false).await.unwrap();
    assert_eq!(show.name, "The Walking Dead");
    assert_eq!(show.show_type.as_deref(), Some("Scripted"));
    assert_eq!(show.language.as_deref(), Some("English"));
    assert!(!show.genres.is_empty());
    assert!(show.externals.is_some());
    let ext = show.externals.unwrap();
    assert_eq!(ext.thetvdb, Some(153021));
    assert_eq!(ext.imdb.as_deref(), Some("tt1520211"));
    assert!(show.image.is_some());
    assert!(show.embedded.is_none());
}

#[tokio::test]
async fn tvmaze_show_embed_episodes() {
    let show = tvmaze_show(&client(), 73, true).await.unwrap();
    assert_eq!(show.name, "The Walking Dead");
    let embedded = show.embedded.unwrap();
    assert!(!embedded.episodes.is_empty());
    let ep = &embedded.episodes[0];
    assert_eq!(ep.season, Some(1));
    assert_eq!(ep.number, Some(1));
    assert!(ep.name.is_some());
}

#[tokio::test]
async fn tvmaze_show_not_found() {
    let result = tvmaze_show(&client(), 0, false).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

// -- tvmaze_show_search --

#[tokio::test]
async fn tvmaze_show_search_success() {
    let results = tvmaze_show_search(&client(), "walking dead").await.unwrap();
    assert!(!results.is_empty());
    assert!(results[0].score > 0.0);
    assert!(results.iter().any(|r| r.show.name.contains("Walking Dead")));
}

#[tokio::test]
async fn tvmaze_show_search_no_hits() {
    let results = tvmaze_show_search(&client(), "zzzxxxyyyqqqnonsense")
        .await
        .unwrap();
    assert!(results.is_empty());
}

// -- tvmaze_show_single_search --

#[tokio::test]
async fn tvmaze_show_single_search_success() {
    let show = tvmaze_show_single_search(&client(), "fargo").await.unwrap();
    assert_eq!(show.name, "Fargo");
}

#[tokio::test]
async fn tvmaze_show_single_search_no_hits() {
    let result = tvmaze_show_single_search(&client(), "zzzxxxyyyqqqnonsense").await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

// -- tvmaze_show_lookup --

#[tokio::test]
async fn tvmaze_show_lookup_by_imdb() {
    let show = tvmaze_show_lookup(&client(), Some("tt1520211"), None)
        .await
        .unwrap();
    assert_eq!(show.name, "The Walking Dead");
}

#[tokio::test]
async fn tvmaze_show_lookup_by_tvdb() {
    let show = tvmaze_show_lookup(&client(), None, Some(153021))
        .await
        .unwrap();
    assert_eq!(show.name, "The Walking Dead");
}

#[tokio::test]
async fn tvmaze_show_lookup_imdb_not_found() {
    let result = tvmaze_show_lookup(&client(), Some("tt0000000"), None).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

#[tokio::test]
async fn tvmaze_show_lookup_tvdb_not_found() {
    let result = tvmaze_show_lookup(&client(), None, Some(999_999_999_999_999_999)).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

#[tokio::test]
async fn tvmaze_show_lookup_tvdb_invalid() {
    let result = tvmaze_show_lookup(&client(), None, Some(0)).await;
    assert!(matches!(
        result,
        Err(EndpointError::InvalidRequest { status: 400, .. })
    ));
}

// -- tvmaze_show_episodes_list --

#[tokio::test]
async fn tvmaze_show_episodes_list_success() {
    let episodes = tvmaze_show_episodes_list(&client(), 73, false)
        .await
        .unwrap();
    assert!(!episodes.is_empty());
    let ep = &episodes[0];
    assert_eq!(ep.season, Some(1));
    assert_eq!(ep.number, Some(1));
    assert!(ep.name.is_some());
    assert!(ep.airdate.is_some());
}

#[tokio::test]
async fn tvmaze_show_episodes_list_not_found() {
    let result = tvmaze_show_episodes_list(&client(), 0, false).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

// -- tvmaze_episodes_by_date --

#[tokio::test]
async fn tvmaze_episodes_by_date_success() {
    let episodes = tvmaze_episodes_by_date(&client(), 73, "2015-02-22")
        .await
        .unwrap();
    assert!(!episodes.is_empty());
    assert!(
        episodes
            .iter()
            .any(|e| e.name.as_deref() == Some("The Distance"))
    );
}

#[tokio::test]
async fn tvmaze_episodes_by_date_bad_id() {
    let result = tvmaze_episodes_by_date(&client(), 0, "2015-02-22").await;
    assert!(result.is_err());
}

#[tokio::test]
async fn tvmaze_episodes_by_date_no_hits() {
    let result = tvmaze_episodes_by_date(&client(), 73, "1900-01-01").await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

// -- tvmaze_episode_by_number --

#[tokio::test]
async fn tvmaze_episode_by_number_success() {
    let ep = tvmaze_episode_by_number(&client(), 73, 5, 11)
        .await
        .unwrap();
    assert_eq!(ep.name.as_deref(), Some("The Distance"));
    assert_eq!(ep.season, Some(5));
    assert_eq!(ep.number, Some(11));
    assert!(ep.airdate.is_some());
}

#[tokio::test]
async fn tvmaze_episode_by_number_not_found() {
    let result = tvmaze_episode_by_number(&client(), 73, 99, 99).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}
