import pytest

from mnamer.exceptions import MnamerNotFoundException
from mnamer.language import Language
from mnamer.metadata import MetadataEpisode
from mnamer.providers import TvMaze
from tests import EPISODE_META, JUNK_TEXT, TEST_DATE, EpisodeMeta

pytestmark = [
    pytest.mark.network,
    pytest.mark.tvmaze,
    pytest.mark.flaky(reruns=1),
]


@pytest.fixture(scope="session")
def provider():
    return TvMaze()


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_season_and_episode(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(
        id_tvmaze=str(meta["id_tvmaze"]),
        season=meta["season"],
        episode=meta["episode"],
    )
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.title == meta["title"]


def test_search_id_tvmaze_and_season_and_episode__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=JUNK_TEXT, season=1, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_date(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=str(meta["id_tvmaze"]), date=meta["date"])
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.title == meta["title"]


def test_search_id_tvmaze_and_date__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=JUNK_TEXT, date=TEST_DATE)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvdb_and_date(meta, provider: TvMaze):
    query = MetadataEpisode(id_tvdb=meta["id_tvdb"], date=meta["date"])
    results = list(provider.search(query))
    assert results
    for result in results:
        assert result.title == meta["title"]


def test_search_id_tvdb_and_date__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvdb=JUNK_TEXT, date=TEST_DATE)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_season(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=str(meta["id_tvmaze"]), season=meta["season"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)
    assert all(result.season == meta["season"] for result in results)


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze_and_episode(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=str(meta["id_tvmaze"]), episode=meta["episode"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)
    assert all(result.episode == meta["episode"] for result in results)


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvmaze(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=str(meta["id_tvmaze"]))
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_id_tvmaze__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvmaze=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_id_tvdb(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(id_tvdb=str(meta["id_tvdb"]))
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_id_tvdb__no_hits(provider: TvMaze):
    query = MetadataEpisode(id_tvdb=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series_and_season_and_episode(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(
        series=meta["series"], season=meta["season"], episode=meta["episode"]
    )
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series_and_season_and_episode__no_hits(provider: TvMaze):
    query = MetadataEpisode(series=JUNK_TEXT, season=1, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series_and_season(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(series=meta["series"], season=meta["season"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series_and_season__no_hits(provider):
    query = MetadataEpisode(series=JUNK_TEXT, season=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series_and_episode(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(series=meta["series"], episode=meta["episode"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series_and_episode__no_hits(provider: TvMaze):
    query = MetadataEpisode(series=JUNK_TEXT, episode=1)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


@pytest.mark.parametrize("meta", EPISODE_META.values(), ids=list(EPISODE_META))
def test_search_series(meta: EpisodeMeta, provider: TvMaze):
    query = MetadataEpisode(series=meta["series"])
    results = list(provider.search(query))
    assert results
    assert any(result.title == meta["title"] for result in results)


def test_search_series__no_hits(provider: TvMaze):
    query = MetadataEpisode(series=JUNK_TEXT)
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search__no_hits(provider: TvMaze):
    query = MetadataEpisode()
    with pytest.raises(MnamerNotFoundException):
        next(provider.search(query))


def test_search__foreign_show_returns_primary_name_when_no_english_aka():
    """Show with only a country=null AKA returns primary name for --language=en."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="59772",
        season=1,
        episode=1,
        language=Language.parse("en"),
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "Schneller Als Die Angst"


def test_search__foreign_show_primary_name_without_language():
    """Foreign show returns primary name when no language set."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="59772",
        season=1,
        episode=1,
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "Schneller Als Die Angst"


def test_search__show_with_ambiguous_akas_returns_primary():
    """Show with only country=null AKAs returns primary name even with language=en."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="92273",  # Morfeusz — AKAs have no country codes
        season=1,
        episode=1,
        language=Language.parse("en"),
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "Morfeusz"  # should NOT return "Morfeus"


def test_search__korean_show_returns_korean_aka():
    """Korean show returns Korean-script AKA when language=ko."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="92451",
        season=1,
        episode=1,
        language=Language.parse("ko"),
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "검사실의 제안"


def test_search__korean_show_returns_primary_without_language():
    """Korean show returns primary English name when no language set."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="92451",
        season=1,
        episode=1,
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "The Prosecutor's Office's Proposal"


def test_search__show_with_no_akas_returns_primary_name():
    """Show with no AKAs returns primary name regardless of requested language."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="50",  # The Lottery — no AKAs, language: English
        season=1,
        episode=1,
        language=Language.parse("en"),
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "The Lottery"


def test_search__unsupported_language_warns_and_returns_primary():
    """Requesting a language with no _LANGUAGE_COUNTRIES mapping warns and returns primary name."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="50",  # The Lottery — simple English show, no AKAs
        season=1,
        episode=1,
        language=Language.parse("ar"),  # Arabic — not in _LANGUAGE_COUNTRIES
    )
    with pytest.warns(UserWarning, match="No TVMaze country mapping for language 'ar'"):
        results = list(provider.search(query))
    assert results
    assert results[0].series == "The Lottery"


def test_search__no_matching_language_aka_returns_primary():
    """Show with AKAs but none matching the requested language returns primary name."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="92451",  # The Prosecutor's Office's Proposal — has KR AKA only
        season=1,
        episode=1,
        language=Language.parse("de"),  # German — no DE AKA exists
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "The Prosecutor's Office's Proposal"


def test_search__multiple_akas_same_country_returns_first():
    """When multiple AKAs exist for the same country, the first one is returned."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="2",  # Person of Interest — two RU AKAs: 'В поле зрения' and 'Подозреваемые'
        season=1,
        episode=1,
        language=Language.parse("ru"),
    )
    results = list(provider.search(query))
    assert results
    assert results[0].series == "В Поле Зрения"  # first RU AKA wins
