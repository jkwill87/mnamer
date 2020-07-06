import pytest
from babelfish import Language as BabelLang

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
        Language("English", "en", "eng"),
        Language("French", "fr", "fra"),
        Language("Spanish", "es", "spa"),
        Language("German", "de", "deu"),
        Language("Hindi", "hi", "hin"),
        Language("Chinese", "zh", "zho"),
        Language("Japanese", "ja", "jpn"),
        Language("Italian", "it", "ita"),
        Language("Russian", "ru", "rus"),
        Language("Arabic", "ar", "ara"),
        Language("Korean", "ko", "kor"),
        Language("Hebrew", "he", "heb"),
        Language("Portuguese", "pt", "por"),
        Language("Swedish", "sv", "swe"),
        Language("Latin", "la", "lat"),
        Language("Ukrainian", "uk", "ukr"),
        Language("Danish", "da", "dan"),
        Language("Persian", "fa", "fas"),
    )
    actual = Language.all()
    assert actual == expected
