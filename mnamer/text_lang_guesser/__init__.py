import logging
from typing import Dict
from mnamer.exceptions import MnamerFailedLangGuesserImport, MnamerNoSuchLangGuesser
from mnamer.language import Language


def guesser(name: str, guess_languages: Dict[str, Language]):
    lower_name = name.lower()
    try:
        if lower_name == "lingua":  # noqa
            from mnamer.text_lang_guesser.lingua import LinguaGuesser

            guesser_cls = LinguaGuesser  # noqa
        elif lower_name == "langdetect":
            from mnamer.text_lang_guesser.langdetect import LangdetectGuesser

            guesser_cls = LangdetectGuesser
        elif lower_name == "langdetect":
            from mnamer.text_lang_guesser.fasttext import FasttextGuesser

            guesser_cls = FasttextGuesser
        elif lower_name == "langid":
            from mnamer.text_lang_guesser.langid import LangidGuesser

            guesser_cls = LangidGuesser
        else:
            raise MnamerNoSuchLangGuesser("Unrecognized language guesser")
    except ImportError as e:
        logging.debug(f"Failed to import text language guesser '{name}'", exc_info=e)
        raise MnamerFailedLangGuesserImport(
            f"Failed to import text language guesser '{name}': {e}"
        )

    try:
        return guesser_cls(guess_languages=guess_languages)
    except Exception as e:
        logging.debug(f"Error trying to instantiate {guesser_cls.__name__}", exc_info=e)
        raise e
