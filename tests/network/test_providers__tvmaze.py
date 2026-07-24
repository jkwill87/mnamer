from typing import cast

import pytest

from mnamer.endpoints import TvMazeShow
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
    """_preferred_name warns when language has no country mapping."""
    series = cast(
        TvMazeShow,
        {
            "name": "The Lottery",
            "_embedded": {"akas": []},
        },
    )
    with pytest.warns(UserWarning, match="No TVMaze country mapping for language 'ar'"):
        result = TvMaze._preferred_name(series, language=Language.parse("ar"))
    assert result == "The Lottery"


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


# ---------------------------------------------------------------------------
# TvMaze._candidate_names — unit tests (no network)
# ---------------------------------------------------------------------------


class TestCandidateNames:
    """Tests for TvMaze._candidate_names static method."""

    def _make_series(self, series_name: str, akas: list[dict]) -> TvMazeShow:
        return cast(
            TvMazeShow,
            {
                "name": series_name,
                "_embedded": {"akas": akas},
            },
        )

    def test_no_language_returns_primary_only(self):
        series = self._make_series(
            "Schneller Als Die Angst",
            [
                {"name": "Faster Than Fear", "country": None},
            ],
        )
        result = TvMaze._candidate_names(series, language=None)
        assert result == ["Schneller Als Die Angst"]

    def test_exact_country_match_returns_single_result(self):
        """Exact country-coded match — no ambiguity, no extra choices."""
        series = self._make_series(
            "Morfeusz",
            [
                {"name": "Morpheus", "country": {"code": "GB"}},
                {"name": "Morphée", "country": {"code": "FR"}},
            ],
        )
        result = TvMaze._candidate_names(series, language=Language.parse("en"))
        assert result == ["Morpheus"]

    def test_no_match_with_null_akas_returns_primary_plus_nulls(self):
        """No country-coded match but country=null AKAs exist — offer choice."""
        series = self._make_series(
            "Schneller Als Die Angst",
            [
                {"name": "Faster Than Fear", "country": None},
                {"name": "Peur Bleue", "country": None},
            ],
        )
        result = TvMaze._candidate_names(series, language=Language.parse("en"))
        assert result == [
            "Schneller Als Die Angst",
            "Faster Than Fear",
            "Peur Bleue",
        ]

    def test_no_match_no_null_akas_returns_primary_only(self):
        """No country-coded match, no null AKAs — silently return primary."""
        series = self._make_series(
            "어게인 마이 라이프",
            [
                {"name": "다시 내 인생", "country": {"code": "KR"}},
            ],
        )
        result = TvMaze._candidate_names(series, language=Language.parse("en"))
        assert result == ["어게인 마이 라이프"]

    def test_empty_akas_returns_primary_only(self):
        series = self._make_series("Some Show", [])
        result = TvMaze._candidate_names(series, language=Language.parse("en"))
        assert result == ["Some Show"]

    def test_missing_embedded_returns_primary_only(self):
        series = cast(TvMazeShow, {"name": "Some Show"})
        result = TvMaze._candidate_names(series, language=Language.parse("en"))
        assert result == ["Some Show"]

    def test_unsupported_language_returns_primary_only(self):
        """Language not in _LANGUAGE_COUNTRIES — falls through to primary."""
        series = self._make_series(
            "какое-то шоу",
            [
                {"name": "Some Show", "country": None},
            ],
        )
        # "ar" is a valid ISO code but not mapped in _LANGUAGE_COUNTRIES
        result = TvMaze._candidate_names(series, language=Language.parse("ar"))
        assert result == ["какое-то шоу"]

    def test_null_aka_not_returned_when_exact_match_exists(self):
        """If exact country match found, null AKAs must not be included."""
        series = self._make_series(
            "Schneller Als Die Angst",
            [
                {"name": "Faster Than Fear", "country": None},
                {"name": "Fear", "country": {"code": "US"}},
            ],
        )
        result = TvMaze._candidate_names(series, language=Language.parse("en"))
        assert result == ["Fear"]
        assert "Faster Than Fear" not in result
        assert "Schneller Als Die Angst" not in result


# ---------------------------------------------------------------------------
# Integration test — network
# ---------------------------------------------------------------------------


@pytest.mark.network
@pytest.mark.tvmaze
@pytest.mark.flaky(reruns=1)
def test_search__null_aka_show_yields_multiple_series_name_candidates():
    """Schneller Als Die Angst (id=59772) has country=null AKA 'Faster Than Fear'.
    With --language=en, both names should appear as separate results."""
    provider = TvMaze(cache=False)
    query = MetadataEpisode(
        id_tvmaze="59772",
        season=1,
        episode=1,
        language=Language.parse("en"),
    )
    results = list(provider.search(query))
    series_names = [r.series for r in results]
    assert "Schneller Als Die Angst" in series_names
    assert "Faster Than Fear" in series_names
