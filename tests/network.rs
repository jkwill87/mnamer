//! Exercises live metadata-provider endpoint integrations.

mod network {
    //! Groups live endpoint tests by provider.

    mod omdb;
    mod tmdb;
    mod tvdb_v3;
    mod tvmaze;
}
