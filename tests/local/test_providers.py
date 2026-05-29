import datetime as dt

import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.language import Language
from mnamer.metadata import MetadataEpisode, MetadataMovie
from mnamer.providers import Omdb, Provider, Tmdb, Tvdb, TvMaze
from mnamer.setting_store import SettingStore
from mnamer.types import ProviderType

pytestmark = pytest.mark.local


OMDB_TITLE = {
    "title": "Example Movie",
    "year": "2020",
    "released": "15 May 2020",
    "plot": "Example plot.",
    "imdb_id": "tt1234567",
}

TMDB_MOVIE = {
    "id": 42,
    "title": "Example Movie",
    "release_date": "2020-05-15",
    "overview": "Example overview.",
    "imdb_id": "tt1234567",
}

TVDB_SERIES = {"data": {"id": 100, "series_name": "Example Series"}}

TVDB_EPISODE = {
    "first_aired": "2020-01-02",
    "aired_episode_number": 2,
    "aired_season": 1,
    "overview": "Example overview.",
    "episode_name": "Episode Two",
}

TVMAZE_SHOW = {
    "id": 200,
    "name": "Example Series",
    "externals": {"thetvdb": 100, "imdb": "tt7654321"},
}

TVMAZE_EPISODE = {
    "airdate": "2020-01-02",
    "number": 2,
    "season": 1,
    "name": "Episode Two",
    "summary": "Example summary.",
}


def test_provider_factory__returns_configured_provider_types():
    settings = SettingStore()

    assert isinstance(Provider.provider_factory(ProviderType.OMDB, settings), Omdb)
    assert isinstance(Provider.provider_factory(ProviderType.TMDB, settings), Tmdb)
    assert isinstance(Provider.provider_factory(ProviderType.TVDB, settings), Tvdb)
    assert isinstance(Provider.provider_factory(ProviderType.TVMAZE, settings), TvMaze)


def test_provider_from_settings__uses_api_key_and_cache_flag():
    settings = SettingStore(api_key_omdb="configured-key", no_cache=True)

    provider = Omdb.from_settings(settings)

    assert provider.api_key == "configured-key"
    assert provider.cache is False


def test_tvdb_from_settings__logs_in_when_cache_is_disabled(mocker):
    mock_login = mocker.patch("mnamer.providers.tvdb_login", return_value="token")
    settings = SettingStore(api_key_tvdb="configured-key", no_cache=True)

    provider = Tvdb.from_settings(settings)

    assert provider.cache is False
    assert provider.token == "token"
    mock_login.assert_called_once_with("configured-key")


def test_omdb_search__id_lookup(mocker):
    mock_title = mocker.patch("mnamer.providers.omdb_title", return_value=OMDB_TITLE)

    result = next(Omdb("key").search(MetadataMovie(id_imdb="tt1234567")))

    assert result.name == "Example Movie"
    assert result.year == 2020
    assert result.id_imdb == "tt1234567"
    assert result.synopsis == "Example plot."
    mock_title.assert_called_once_with("key", "tt1234567", cache=True)


def test_omdb_search__fallback_year_and_na_synopsis(mocker):
    mocker.patch(
        "mnamer.providers.omdb_title",
        return_value={
            "title": "Fallback Movie",
            "year": "1999",
            "plot": "N/A",
            "imdb_id": "tt7654321",
        },
    )

    result = next(Omdb("key").search(MetadataMovie(id_imdb="tt7654321")))

    assert result.year == 1999
    assert result.synopsis is None


def test_omdb_search__title_filters_year_and_stops_on_not_found(mocker):
    mock_search = mocker.patch(
        "mnamer.providers.omdb_search",
        side_effect=[
            {
                "search": [
                    {"imdb_id": "tt0000001", "title": "Old Hit", "year": "2010"},
                    {
                        "imdb_id": "tt1234567",
                        "title": "Example Movie",
                        "year": "2020",
                    },
                ],
                "total_results": "2",
            },
            MnamerNotFoundException,
        ],
    )
    mock_title = mocker.patch("mnamer.providers.omdb_title", return_value=OMDB_TITLE)

    results = list(Omdb("key").search(MetadataMovie(name="Example", year="2020")))

    assert [result.id_imdb for result in results] == ["tt1234567"]
    assert mock_search.call_count == 2
    mock_title.assert_called_once_with("key", "tt1234567", cache=True)


def test_omdb_search__missing_query():
    with pytest.raises(MnamerNotFoundException):
        next(Omdb("key").search(MetadataMovie()))


def test_omdb_search__no_hits(mocker):
    mocker.patch("mnamer.providers.omdb_search", side_effect=MnamerNotFoundException)

    with pytest.raises(MnamerNotFoundException):
        next(Omdb("key").search(MetadataMovie(name="Missing")))


def test_tmdb_search__id_lookup_forwards_language_and_cache(mocker):
    mock_movies = mocker.patch("mnamer.providers.tmdb_movies", return_value=TMDB_MOVIE)
    language = Language.parse("en")

    result = next(
        Tmdb("key", cache=False).search(MetadataMovie(id_tmdb="42", language=language))
    )

    assert result.name == "Example Movie"
    assert result.year == 2020
    assert result.id_tmdb == "42"
    assert result.id_imdb == "tt1234567"
    mock_movies.assert_called_once_with("key", "42", language, False)


def test_tmdb_search__name_skips_malformed_and_undated_results(mocker):
    mocker.patch(
        "mnamer.providers.tmdb_search_movies",
        return_value={
            "results": [
                {"id": 1, "title": "Undated Movie", "release_date": ""},
                {"id": 2, "release_date": "2020-01-01"},
                TMDB_MOVIE,
            ],
            "total_pages": 1,
            "total_results": 3,
        },
    )

    results = list(Tmdb("key").search(MetadataMovie(name="Example")))

    assert [result.id_tmdb for result in results] == ["42"]


def test_tmdb_search__name_stops_at_page_limit(mocker):
    mock_search = mocker.patch(
        "mnamer.providers.tmdb_search_movies",
        return_value={"results": [], "total_pages": 7, "total_results": 7},
    )

    with pytest.raises(MnamerNotFoundException):
        next(Tmdb("key").search(MetadataMovie(name="Missing")))

    assert mock_search.call_count == 5


def test_tmdb_search__missing_query():
    with pytest.raises(MnamerNotFoundException):
        next(Tmdb("key").search(MetadataMovie()))


def test_tmdb_search__no_hits(mocker):
    mocker.patch(
        "mnamer.providers.tmdb_search_movies",
        side_effect=MnamerNotFoundException,
    )

    with pytest.raises(MnamerNotFoundException):
        next(Tmdb("key").search(MetadataMovie(name="Missing")))


def test_tvdb_search__lazy_login_and_id_search(mocker):
    mock_login = mocker.patch("mnamer.providers.tvdb_login", return_value="token")
    mock_series = mocker.patch(
        "mnamer.providers.tvdb_series_id", return_value=TVDB_SERIES
    )
    mock_episodes = mocker.patch(
        "mnamer.providers.tvdb_series_id_episodes_query",
        return_value={"data": [TVDB_EPISODE], "links": {"last": 1}},
    )
    provider = Tvdb("key")

    result = next(provider.search(MetadataEpisode(id_tvdb="100", season=1, episode=2)))

    assert result.series == "Example Series"
    assert result.title == "Episode Two"
    assert result.id_tvdb == "100"
    mock_login.assert_called_once_with("key")
    mock_series.assert_called_once_with("token", "100", language=None, cache=True)
    mock_episodes.assert_called_once_with(
        "token",
        "100",
        2,
        1,
        language=None,
        page=1,
        cache=True,
    )


def test_tvdb_search__paginates_and_skips_bad_episode_rows(mocker):
    mocker.patch("mnamer.providers.tvdb_login", return_value="token")
    mocker.patch("mnamer.providers.tvdb_series_id", return_value=TVDB_SERIES)
    mock_episodes = mocker.patch(
        "mnamer.providers.tvdb_series_id_episodes_query",
        side_effect=[
            {
                "data": [{"first_aired": "2020-01-01"}],
                "links": {"last": 2},
            },
            {"data": [TVDB_EPISODE], "links": {"last": 2}},
        ],
    )

    results = list(Tvdb("key").search(MetadataEpisode(id_tvdb="100")))

    assert [result.title for result in results] == ["Episode Two"]
    assert mock_episodes.call_count == 2


def test_tvdb_search__series_tries_candidate_ids(mocker):
    provider = Tvdb("key")
    provider.token = "token"
    mocker.patch(
        "mnamer.providers.tvdb_search_series",
        return_value={"data": [{"id": 1}, {"id": 100}]},
    )
    mock_search_id = mocker.patch.object(
        provider,
        "_search_id",
        side_effect=[
            MnamerNotFoundException,
            [MetadataEpisode(id_tvdb="100", series="Example Series", season=1)],
        ],
    )

    results = list(provider.search(MetadataEpisode(series="Example Series")))

    assert [result.id_tvdb for result in results] == ["100"]
    assert mock_search_id.call_count == 2


def test_tvdb_search__date_filters_id_results(mocker):
    provider = Tvdb("key")
    provider.token = "token"
    mocker.patch.object(
        provider,
        "_search_id",
        return_value=[
            MetadataEpisode(id_tvdb="100", date=dt.date(2020, 1, 1)),
            MetadataEpisode(id_tvdb="100", date=dt.date(2020, 1, 2)),
        ],
    )

    results = list(
        provider.search(MetadataEpisode(id_tvdb="100", date=dt.date(2020, 1, 2)))
    )

    assert [result.date for result in results] == [dt.date(2020, 1, 2)]


def test_tvdb_search__missing_query():
    provider = Tvdb("key")
    provider.token = "token"

    with pytest.raises(MnamerNotFoundException):
        next(provider.search(MetadataEpisode()))


def test_tvmaze_search__tvmaze_id_season_episode(mocker):
    mocker.patch("mnamer.providers.tvmaze_show", return_value=TVMAZE_SHOW)
    mocker.patch(
        "mnamer.providers.tvmaze_episode_by_number",
        return_value=TVMAZE_EPISODE,
    )

    result = next(
        TvMaze().search(MetadataEpisode(id_tvmaze="200", season=1, episode=2))
    )

    assert result.series == "Example Series"
    assert result.title == "Episode Two"
    assert result.id_tvmaze == "200"
    assert result.id_tvdb == "100"


def test_tvmaze_search__tvdb_id_date_lookup(mocker):
    mocker.patch("mnamer.providers.tvmaze_show_lookup", return_value=TVMAZE_SHOW)
    mocker.patch(
        "mnamer.providers.tvmaze_episodes_by_date",
        return_value=[TVMAZE_EPISODE],
    )

    result = next(
        TvMaze().search(MetadataEpisode(id_tvdb="100", date=dt.date(2020, 1, 2)))
    )

    assert result.id_tvmaze == "200"
    assert result.id_tvdb == "100"
    assert result.date == dt.date(2020, 1, 2)


def test_tvmaze_search__id_filters_episode_list(mocker):
    mocker.patch("mnamer.providers.tvmaze_show", return_value=TVMAZE_SHOW)
    mocker.patch(
        "mnamer.providers.tvmaze_show_episodes_list",
        return_value=[
            {**TVMAZE_EPISODE, "number": 1, "name": "Episode One"},
            TVMAZE_EPISODE,
        ],
    )

    results = list(TvMaze().search(MetadataEpisode(id_tvmaze="200", episode=2)))

    assert [result.title for result in results] == ["Episode Two"]


def test_tvmaze_search__series_season_episode_tries_first_three(mocker):
    shows = [
        {"show": {**TVMAZE_SHOW, "id": 201}},
        {"show": TVMAZE_SHOW},
        {"show": {**TVMAZE_SHOW, "id": 202}},
        {"show": {**TVMAZE_SHOW, "id": 203}},
    ]
    mocker.patch("mnamer.providers.tvmaze_show_search", return_value=shows)
    mock_episode = mocker.patch(
        "mnamer.providers.tvmaze_episode_by_number",
        side_effect=[
            MnamerNotFoundException,
            TVMAZE_EPISODE,
            MnamerNotFoundException,
        ],
    )

    results = list(
        TvMaze().search(MetadataEpisode(series="Example Series", season=1, episode=2))
    )

    assert [result.id_tvmaze for result in results] == ["200"]
    assert mock_episode.call_count == 3


def test_tvmaze_search__series_filters_episode_list(mocker):
    mocker.patch(
        "mnamer.providers.tvmaze_show_search",
        return_value=[{"show": TVMAZE_SHOW}],
    )
    mocker.patch(
        "mnamer.providers.tvmaze_show_episodes_list",
        return_value=[
            {**TVMAZE_EPISODE, "season": 2, "name": "Wrong Season"},
            TVMAZE_EPISODE,
        ],
    )

    results = list(TvMaze().search(MetadataEpisode(series="Example Series", season=1)))

    assert [result.title for result in results] == ["Episode Two"]


def test_tvmaze_search__missing_query():
    with pytest.raises(MnamerNotFoundException):
        next(TvMaze().search(MetadataEpisode()))


def test_tvmaze_search__no_hits(mocker):
    mocker.patch(
        "mnamer.providers.tvmaze_show_search",
        side_effect=MnamerNotFoundException,
    )

    with pytest.raises(MnamerNotFoundException):
        next(TvMaze().search(MetadataEpisode(series="Missing")))
