import pytest
from babelfish import Language as BabelLang  # type: ignore

from mnamer.language import Language


@pytest.mark.parametrize("value", ("english", "en", "eng"))
def test_language_parse__str(value):
    expected = Language("English", "en", "eng")
    actual = Language.parse(value)
    assert actual == expected


def test_language_parse__bl():
    expected = Language("English", "en", "eng")
    actual = Language.parse(BabelLang("eng"))
    assert actual == expected


def test_language_all():
    expected = (
        Language("Arabic", "ar", "ara"),
        Language("Chinese", "zh", "zho"),
        Language("Croatian", "hr", "hrv"),
        Language("Czech", "cs", "ces"),
        Language("Danish", "da", "dan"),
        Language("English", "en", "eng"),
        Language("French", "fr", "fra"),
        Language("German", "de", "deu"),
        Language("Greek", "el", "ell"),
        Language("Hebrew", "he", "heb"),
        Language("Hindi", "hi", "hin"),
        Language("Italian", "it", "ita"),
        Language("Japanese", "ja", "jpn"),
        Language("Korean", "ko", "kor"),
        Language("Latin", "la", "lat"),
        Language("Persian", "fa", "fas"),
        Language("Portuguese", "pt", "por"),
        Language("Russian", "ru", "rus"),
        Language("Slovenian", "sl", "slv"),
        Language("Spanish", "es", "spa"),
        Language("Swedish", "sv", "swe"),
        Language("Turkish", "tr", "tur"),
        Language("Ukrainian", "uk", "ukr"),
    )
    actual = Language.all()
    assert actual == expected
