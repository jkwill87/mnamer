//! Verifies live TMDb endpoint behavior.

use mnamer::net::endpoint::tmdb::*;
use mnamer::net::endpoint::{self as endpoint, EndpointError};

fn client() -> endpoint::ApiClient {
    endpoint::build_client(false).unwrap()
}

fn api_key() -> String {
    std::env::var("API_KEY_TMDB").expect("API_KEY_TMDB must be set")
}

// -- tmdb_find --

#[tokio::test]
async fn tmdb_find_imdb_success() {
    let result = tmdb_find(&client(), &api_key(), "tt0089218", "imdb_id", None)
        .await
        .unwrap();
    assert!(!result.movie_results.is_empty());
    let movie = &result.movie_results[0];
    assert_eq!(movie.title, "The Goonies");
    assert!(movie.id > 0);
    assert!(movie.overview.is_some());
    assert!(movie.release_date.is_some());
}

#[tokio::test]
async fn tmdb_find_not_found() {
    let result = tmdb_find(&client(), &api_key(), "tt0000000", "imdb_id", None)
        .await
        .unwrap();
    assert!(result.movie_results.is_empty());
}

#[tokio::test]
async fn tmdb_find_bad_api_key() {
    let result = tmdb_find(&client(), "invalid_key", "tt0089218", "imdb_id", None).await;
    assert!(matches!(result, Err(EndpointError::InvalidRequest { .. })));
}

#[tokio::test]
async fn tmdb_find_language() {
    let russian = mediakit::meta::fields::Language {
        name: "russian",
        iso_639_1: "ru",
        iso_639_3: "rus",
    };
    let result = tmdb_find(&client(), &api_key(), "tt0089218", "imdb_id", Some(russian))
        .await
        .unwrap();
    assert!(!result.movie_results.is_empty());
}

// -- tmdb_movies --

#[tokio::test]
async fn tmdb_movies_success() {
    let result = tmdb_movies(&client(), &api_key(), 9340, None)
        .await
        .unwrap();
    assert_eq!(result.title, "The Goonies");
    assert!(result.imdb_id.is_some());
    assert!(result.overview.is_some());
    assert!(result.release_date.is_some());
    assert!(result.runtime.is_some());
    assert!(result.genres.is_some());
}

#[tokio::test]
async fn tmdb_movies_not_found() {
    let result = tmdb_movies(&client(), &api_key(), 0, None).await;
    assert!(matches!(result, Err(EndpointError::NotFound { .. })));
}

#[tokio::test]
async fn tmdb_movies_bad_api_key() {
    let result = tmdb_movies(&client(), "invalid_key", 9340, None).await;
    assert!(matches!(result, Err(EndpointError::InvalidRequest { .. })));
}

#[tokio::test]
async fn tmdb_movies_language() {
    let russian = mediakit::meta::fields::Language {
        name: "russian",
        iso_639_1: "ru",
        iso_639_3: "rus",
    };
    let result = tmdb_movies(&client(), &api_key(), 9340, Some(russian))
        .await
        .unwrap();
    assert_eq!(result.id, 9340);
}

// -- tmdb_search_movies --

#[tokio::test]
async fn tmdb_search_movies_success() {
    let result = tmdb_search_movies(
        &client(),
        &api_key(),
        "The Goonies",
        None,
        None,
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert!(!result.results.is_empty());
    assert!(result.results.iter().any(|m| m.title == "The Goonies"));
    assert!(result.total_results > 0);
}

#[tokio::test]
async fn tmdb_search_movies_with_year() {
    let result = tmdb_search_movies(
        &client(),
        &api_key(),
        "The Goonies",
        Some(1985),
        None,
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert!(!result.results.is_empty());
    assert!(result.results.iter().any(|m| {
        m.release_date
            .as_deref()
            .is_some_and(|d| d.starts_with("1985"))
    }));
}

#[tokio::test]
async fn tmdb_search_movies_no_results() {
    let result = tmdb_search_movies(
        &client(),
        &api_key(),
        "zzzxxxyyyqqqnonsense",
        None,
        None,
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert!(result.results.is_empty());
    assert_eq!(result.total_results, 0);
}

#[tokio::test]
async fn tmdb_search_movies_bad_api_key() {
    let result = tmdb_search_movies(
        &client(),
        "invalid_key",
        "test",
        None,
        None,
        None,
        None,
        None,
    )
    .await;
    assert!(matches!(result, Err(EndpointError::InvalidRequest { .. })));
}

#[tokio::test]
async fn tmdb_search_movies_language() {
    let russian = mediakit::meta::fields::Language {
        name: "russian",
        iso_639_1: "ru",
        iso_639_3: "rus",
    };
    let result = tmdb_search_movies(
        &client(),
        &api_key(),
        "The Goonies",
        None,
        Some(russian),
        None,
        None,
        None,
    )
    .await
    .unwrap();
    assert!(!result.results.is_empty());
}
