//! Verifies provider wire response models.

use super::*;

#[test]
fn deserialize_omdb_title_result() {
    let json = r#"{
        "Title": "The Matrix",
        "Year": "1999",
        "Rated": "R",
        "Released": "31 Mar 1999",
        "Runtime": "136 min",
        "Genre": "Action, Sci-Fi",
        "Director": "Lana Wachowski, Lilly Wachowski",
        "Writer": "Lilly Wachowski, Lana Wachowski",
        "Actors": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss",
        "Plot": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth.",
        "Language": "English",
        "Country": "United States, Australia",
        "Awards": "Won 4 Oscars. 42 wins & 52 nominations total",
        "Poster": "https://example.com/poster.jpg",
        "Ratings": [
            {"Source": "Internet Movie Database", "Value": "8.7/10"},
            {"Source": "Rotten Tomatoes", "Value": "83%"}
        ],
        "Metascore": "73",
        "imdbRating": "8.7",
        "imdbVotes": "1,900,000",
        "imdbID": "tt0133093",
        "Type": "movie",
        "Response": "True"
    }"#;
    let result: omdb::TitleResult = serde_json::from_str(json).unwrap();
    assert_eq!(result.title, "The Matrix");
    assert_eq!(result.year, "1999");
    assert_eq!(result.imdb_id.as_deref(), Some("tt0133093"));
    assert_eq!(result.media_type.as_deref(), Some("movie"));
    assert_eq!(result.ratings.as_ref().unwrap().len(), 2);
    assert_eq!(result.response, "True");
}

#[test]
fn deserialize_omdb_search_response() {
    let json = r#"{
        "Search": [
            {"Title": "The Matrix", "Year": "1999", "imdbID": "tt0133093", "Type": "movie", "Poster": "N/A"},
            {"Title": "The Matrix Reloaded", "Year": "2003", "imdbID": "tt0234215", "Type": "movie", "Poster": "N/A"}
        ],
        "totalResults": "2",
        "Response": "True"
    }"#;
    let result: omdb::SearchResponse = serde_json::from_str(json).unwrap();
    assert_eq!(result.response, "True");
    assert_eq!(result.total_results.as_deref(), Some("2"));
    let items = result.search.unwrap();
    assert_eq!(items.len(), 2);
    assert_eq!(items[0].imdb_id, "tt0133093");
}

#[test]
fn deserialize_omdb_error_response() {
    let json = r#"{"Response": "False", "Error": "Movie not found!"}"#;
    let result: omdb::ErrorResponse = serde_json::from_str(json).unwrap();
    assert_eq!(result.response, "False");
    assert_eq!(result.error.as_deref(), Some("Movie not found!"));
}

#[test]
fn deserialize_tmdb_find_response() {
    let json = r#"{
        "movie_results": [{
            "id": 603,
            "title": "The Matrix",
            "original_title": "The Matrix",
            "overview": "Set in the 22nd century...",
            "release_date": "1999-03-30",
            "poster_path": "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
            "adult": false,
            "genre_ids": [28, 878],
            "original_language": "en",
            "popularity": 45.2,
            "vote_average": 8.2,
            "vote_count": 22000
        }],
        "tv_results": [],
        "tv_episode_results": [],
        "tv_season_results": [],
        "person_results": []
    }"#;
    let result: tmdb::FindResponse = serde_json::from_str(json).unwrap();
    assert_eq!(result.movie_results.len(), 1);
    assert_eq!(result.movie_results[0].id, 603);
    assert_eq!(result.movie_results[0].title, "The Matrix");
}

#[test]
fn deserialize_tmdb_movie_details() {
    let json = r#"{
        "id": 603,
        "title": "The Matrix",
        "original_title": "The Matrix",
        "overview": "Set in the 22nd century...",
        "release_date": "1999-03-30",
        "imdb_id": "tt0133093",
        "runtime": 136,
        "budget": 63000000,
        "revenue": 463517383,
        "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}],
        "poster_path": "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "status": "Released",
        "tagline": "Welcome to the Real World."
    }"#;
    let result: tmdb::MovieDetails = serde_json::from_str(json).unwrap();
    assert_eq!(result.id, 603);
    assert_eq!(result.imdb_id.as_deref(), Some("tt0133093"));
    assert_eq!(result.runtime, Some(136));
    let genres = result.genres.unwrap();
    assert_eq!(genres.len(), 2);
    assert_eq!(genres[0].name, "Action");
}

#[test]
fn deserialize_tmdb_search_movies_response() {
    let json = r#"{
        "page": 1,
        "results": [
            {"id": 603, "title": "The Matrix", "overview": "...", "release_date": "1999-03-30", "popularity": 45.2, "vote_average": 8.2, "vote_count": 22000}
        ],
        "total_pages": 1,
        "total_results": 1
    }"#;
    let result: tmdb::SearchMoviesResponse = serde_json::from_str(json).unwrap();
    assert_eq!(result.page, 1);
    assert_eq!(result.total_results, 1);
    assert_eq!(result.results[0].id, 603);
}

#[test]
fn deserialize_tvdb_v3_episode() {
    let json = r#"{
        "data": {
            "id": 5765070,
            "airedEpisodeNumber": 11,
            "airedSeason": 5,
            "airedSeasonID": 570070,
            "episodeName": "The Distance",
            "firstAired": "2015-02-22",
            "overview": "Rick and the group are faced with a new challenge.",
            "seriesId": 153021,
            "imdbId": "tt3866840",
            "absoluteNumber": 60,
            "isMovie": 0
        }
    }"#;
    let result: tvdb_v3::DataResponse<tvdb_v3::Episode> = serde_json::from_str(json).unwrap();
    assert_eq!(result.data.id, 5765070);
    assert_eq!(result.data.aired_episode_number, Some(11));
    assert_eq!(result.data.aired_season, Some(5));
    assert_eq!(result.data.episode_name.as_deref(), Some("The Distance"));
    assert_eq!(result.data.first_aired.as_deref(), Some("2015-02-22"));
    assert_eq!(result.data.imdb_id.as_deref(), Some("tt3866840"));
}

#[test]
fn deserialize_tvdb_v3_series() {
    let json = r#"{
        "data": {
            "id": 153021,
            "seriesName": "The Walking Dead",
            "overview": "Sheriff's Deputy Rick Grimes leads a group of survivors.",
            "firstAired": "2010-10-31",
            "status": "Ended",
            "network": "AMC",
            "genre": ["Action", "Drama", "Horror"],
            "runtime": "60"
        }
    }"#;
    let result: tvdb_v3::DataResponse<tvdb_v3::Series> = serde_json::from_str(json).unwrap();
    assert_eq!(result.data.id, 153021);
    assert_eq!(result.data.series_name.as_deref(), Some("The Walking Dead"));
    assert_eq!(result.data.genre.as_ref().unwrap().len(), 3);
}

#[test]
fn deserialize_tvdb_v3_paginated_episodes() {
    let json = r#"{
        "data": [
            {"id": 1, "airedEpisodeNumber": 1, "airedSeason": 1, "episodeName": "Pilot"},
            {"id": 2, "airedEpisodeNumber": 2, "airedSeason": 1, "episodeName": "Guts"}
        ],
        "links": {
            "first": 1,
            "last": 3,
            "next": 2,
            "prev": null
        }
    }"#;
    let result: tvdb_v3::DataResponse<Vec<tvdb_v3::Episode>> = serde_json::from_str(json).unwrap();
    assert_eq!(result.data.len(), 2);
    let links = result.links.unwrap();
    assert_eq!(links.first, Some(1));
    assert_eq!(links.last, Some(3));
    assert_eq!(links.next, Some(2));
    assert!(links.prev.is_none());
}

#[test]
fn deserialize_tvmaze_show() {
    let json = r#"{
        "id": 73,
        "name": "The Walking Dead",
        "type": "Scripted",
        "language": "English",
        "genres": ["Drama", "Action", "Horror"],
        "status": "Ended",
        "runtime": 60,
        "premiered": "2010-10-31",
        "ended": "2022-11-20",
        "officialSite": "https://www.amc.com/shows/the-walking-dead",
        "schedule": {"time": "21:00", "days": ["Sunday"]},
        "rating": {"average": 8.2},
        "weight": 99,
        "network": {"id": 20, "name": "AMC", "country": {"name": "United States", "code": "US", "timezone": "America/New_York"}},
        "externals": {"tvrage": 25056, "thetvdb": 153021, "imdb": "tt1520211"},
        "image": {"medium": "https://example.com/medium.jpg", "original": "https://example.com/original.jpg"},
        "summary": "<p>The Walking Dead is an American horror drama.</p>"
    }"#;
    let result: tvmaze::Show = serde_json::from_str(json).unwrap();
    assert_eq!(result.id, 73);
    assert_eq!(result.name, "The Walking Dead");
    assert_eq!(result.show_type.as_deref(), Some("Scripted"));
    assert_eq!(result.genres, vec!["Drama", "Action", "Horror"]);
    let externals = result.externals.unwrap();
    assert_eq!(externals.thetvdb, Some(153021));
    assert_eq!(externals.imdb.as_deref(), Some("tt1520211"));
    let network = result.network.unwrap();
    assert_eq!(network.name, "AMC");
    assert_eq!(network.country.unwrap().code, "US");
}

#[test]
fn deserialize_tvmaze_episode() {
    let json = r#"{
        "id": 578663,
        "name": "The Distance",
        "season": 5,
        "number": 11,
        "type": "regular",
        "airdate": "2015-02-22",
        "airtime": "21:00",
        "airstamp": "2015-02-23T02:00:00+00:00",
        "runtime": 60,
        "summary": "<p>Rick and the group are faced with a new challenge.</p>"
    }"#;
    let result: tvmaze::Episode = serde_json::from_str(json).unwrap();
    assert_eq!(result.id, 578663);
    assert_eq!(result.name.as_deref(), Some("The Distance"));
    assert_eq!(result.season, Some(5));
    assert_eq!(result.number, Some(11));
    assert_eq!(result.airdate.as_deref(), Some("2015-02-22"));
}

#[test]
fn deserialize_tvmaze_search_result() {
    let json = r#"[
        {"score": 18.2, "show": {"id": 73, "name": "The Walking Dead", "genres": [], "summary": null}},
        {"score": 12.1, "show": {"id": 2710, "name": "Fear the Walking Dead", "genres": [], "summary": null}}
    ]"#;
    let result: Vec<tvmaze::SearchResult> = serde_json::from_str(json).unwrap();
    assert_eq!(result.len(), 2);
    assert_eq!(result[0].show.id, 73);
    assert_eq!(result[1].show.name, "Fear the Walking Dead");
}

#[test]
fn deserialize_tvmaze_show_with_embedded_episodes() {
    let json = r#"{
        "id": 73,
        "name": "The Walking Dead",
        "genres": [],
        "_embedded": {
            "episodes": [
                {"id": 1, "name": "Days Gone Bye", "season": 1, "number": 1, "airdate": "2010-10-31"},
                {"id": 2, "name": "Guts", "season": 1, "number": 2, "airdate": "2010-11-07"}
            ]
        }
    }"#;
    let result: tvmaze::Show = serde_json::from_str(json).unwrap();
    let embedded = result.embedded.unwrap();
    assert_eq!(embedded.episodes.len(), 2);
    assert_eq!(embedded.episodes[0].name.as_deref(), Some("Days Gone Bye"));
}
