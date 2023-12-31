import logging
from typing import Dict
from mnamer.exceptions import (
    MnamerFailedLangGuesserInstantiation,
    MnamerNoSuchLangGuesser,
)
from mnamer.language import Language
from importlib import import_module


def _import_module(dotted_module_name: str):
    try:
        return import_module(dotted_module_name)
    except ImportError as e:
        logging.debug(f"Failed to import {dotted_module_name}: {e}", exc_info=e)
    return None


possible_guessers = (
    ("lingua", "mnamer.text_lang_guesser.lingua.LinguaGuesser"),
    ("langdetect", "mnamer.text_lang_guesser.langdetect.LangdetectGuesser"),
    ("fasttext", "mnamer.text_lang_guesser.fasttext.FasttextGuesser"),
    ("langid", "mnamer.text_lang_guesser.langid.LangidGuesser"),
)

available_guessers = {}
for name, module_class in possible_guessers:
    module_name, classname = module_class.rsplit(".", 1)
    mod = _import_module(module_name)
    if mod:
        try:
            cls = getattr(mod, classname)
        except AttributeError as e:
            logging.debug(
                f"Failed to load class {classname} from module {mod}: {e}", exc_info=e
            )
            continue
        available_guessers[name] = cls


def guesser(name: str, guess_languages: Dict[str, Language]):
    if name not in available_guessers:
        raise MnamerNoSuchLangGuesser("Unrecognized language guesser")
    try:
        return available_guessers[name](guess_languages=guess_languages)
    except Exception as e:
        class_name = available_guessers[name].__name__
        logging.debug(
            f"Error trying to instantiate {class_name}",
            exc_info=e,
        )
        raise MnamerFailedLangGuesserInstantiation(
            f"Failed creating guesser {class_name}"
        )
