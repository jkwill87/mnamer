//! Verifies live OMDb endpoint behavior.

use mnamer::net::endpoint::omdb::*;
use mnamer::net::endpoint::{self as endpoint, EndpointError};

fn client() -> endpoint::ApiClient {
    endpoint::build_client(false).unwrap()
}

fn api_key() -> String {
    std::env::var("API_KEY_OMDB").expect("API_KEY_OMDB must be set")
}

// -- omdb_title --

#[tokio::test]
async fn omdb_title_by_imdb_id() {
    let result = omdb_title(
        &client(),
        &api_key(),
        Some("tt0387808"),
        None,
        None,
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert_eq!(result.title, "Idiocracy");
    assert_eq!(result.year, "2006");
    assert_eq!(result.imdb_id.as_deref(), Some("tt0387808"));
    assert_eq!(result.media_type.as_deref(), Some("movie"));
    assert_eq!(result.response, "True");
    assert!(result.plot.is_some());
    assert!(result.poster.is_some());
}

#[tokio::test]
async fn omdb_title_by_name() {
    let result = omdb_title(
        &client(),
        &api_key(),
        None,
        Some("Citizen Kane"),
        None,
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert_eq!(result.title, "Citizen Kane");
    assert_eq!(result.year, "1941");
}

#[tokio::test]
async fn omdb_title_series() {
    let result = omdb_title(
        &client(),
        &api_key(),
        Some("tt1520211"),
        None,
        None,
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert_eq!(result.title, "The Walking Dead");
    assert_eq!(result.media_type.as_deref(), Some("series"));
}

#[tokio::test]
async fn omdb_title_not_found() {
    let result = omdb_title(
        &client(),
        &api_key(),
        None,
        Some("zzzxxxyyyqqqnonsense"),
        None,
        None,
        None,
        None,
    )
    .await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

#[tokio::test]
async fn omdb_title_bad_imdb_id() {
    let result = omdb_title(
        &client(),
        &api_key(),
        Some("tt9999999"),
        None,
        None,
        None,
        None,
        None,
    )
    .await;
    assert!(result.is_err());
}

#[tokio::test]
async fn omdb_title_bad_api_key() {
    let result = omdb_title(
        &client(),
        "invalid_key",
        Some("tt0387808"),
        None,
        None,
        None,
        None,
        None,
    )
    .await;
    assert!(matches!(result, Err(EndpointError::InvalidRequest { .. })));
}

// -- omdb_search --

#[tokio::test]
async fn omdb_search_movie() {
    let result = omdb_search(&client(), &api_key(), "matrix", None, Some("movie"), None)
        .await
        .unwrap();
    assert_eq!(result.response, "True");
    let items = result.search.unwrap();
    assert!(!items.is_empty());
    assert!(items.iter().all(|i| i.media_type == "movie"));
    // Validate search item fields
    let item = &items[0];
    assert!(!item.title.is_empty());
    assert!(!item.year.is_empty());
    assert!(!item.imdb_id.is_empty());
}

#[tokio::test]
async fn omdb_search_series() {
    let result = omdb_search(&client(), &api_key(), "fargo", None, Some("series"), None)
        .await
        .unwrap();
    let items = result.search.unwrap();
    assert!(items.iter().all(|i| i.media_type == "series"));
}

#[tokio::test]
async fn omdb_search_with_year() {
    let result = omdb_search(&client(), &api_key(), "batman", Some(2022), None, None)
        .await
        .unwrap();
    let items = result.search.unwrap();
    assert!(!items.is_empty());
    assert!(items.iter().any(|i| i.year.contains("2022")));
}

#[tokio::test]
async fn omdb_search_no_hits() {
    let result = omdb_search(
        &client(),
        &api_key(),
        "zzzxxxyyyqqqnonsense",
        None,
        None,
        None,
    )
    .await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

#[tokio::test]
async fn omdb_search_bad_api_key() {
    let result = omdb_search(&client(), "invalid_key", "matrix", None, None, None).await;
    assert!(matches!(result, Err(EndpointError::InvalidRequest { .. })));
}

#[tokio::test]
async fn omdb_search_pagination() {
    let page1 = omdb_search(&client(), &api_key(), "batman", None, None, Some(1))
        .await
        .unwrap();
    let page2 = omdb_search(&client(), &api_key(), "batman", None, None, Some(2))
        .await
        .unwrap();
    let items1 = page1.search.unwrap();
    let items2 = page2.search.unwrap();
    assert_ne!(items1[0].imdb_id, items2[0].imdb_id);
}
