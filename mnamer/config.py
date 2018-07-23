from copy import deepcopy
from json import dumps

from attr import attrib, attrs, fields_dict, validate, validators

from mnamer.constants import DIRECTIVE_KEYS, PREFERENCE_KEYS
from mnamer.exceptions import MnamerConfigException
from mnamer.utils import config_find, config_load, merge_dicts


@attrs
class Configuration:
    ## General Prefereneces
    batch = attrib(False)
    blacklist = attrib((".*sample.*", "^RARBG.*"))
    extmask = attrib(("avi", "m4v", "mp4", "mkv", "ts", "wmv"))
    hits = attrib(15)
    recurse = attrib(False)
    scene = attrib(False)
    verbose = attrib(False)

    ## Movie related
    movie_api = attrib("tmdb")
    movie_destination = attrib("")
    movie_template = attrib("<$title >" "<($year)>" "<$extension>")

    ## Television related
    television_api = attrib("tvdb")
    televsion_destination = attrib("")
    television_template = (
        attrib(
            (
                "<$series - >"
                "< - S$season>"
                "<E$episode - >"
                "< - $title>"
                "<$extension>"
            )
        ),
    )

    ## API Keys -- consider using your own or IMDb if limits are hit
    api_key_tmdb = attrib("db972a607f2760bb19ff8bb34074b4c7")
    api_key_tvdb = attrib("E69C7A2CEF2F3152")

    # Directives
    id = attrib(None)
    media = attrib(None)
    test = attrib(None)
    version = attrib(None)

    def load_file(self):
        json_file = config_find()
        json_data = config_load(json_file)
        for key in PREFERENCE_KEYS:
            value = json_data.get(key)
            if value is not None:
                setattr(self, key, value)
        return json_file

    @property
    def preference_dict(self):
        return {
            key: value
            for key, value in fields_dict(self).items()
            if key in PREFERENCE_KEYS
        }

    @property
    def preference_json(self):
        return dumps(
            self.preference_dict, sort_keys=True, skipkeys=True, allow_nan=False
        )

    @property
    def directive_dict(self):
        return {
            key: value
            for key, value in fields_dict(self).items()
            if key in DIRECTIVE_KEYS
        }

    @property
    def directive_json(self):
        return dumps(
            self.directive_dict, sort_keys=True, skipkeys=True, allow_nan=False
        )

    @property
    def config_dict(self):
        return fields_dict(
            merge_dicts(self.preference_dict, self.directive_dict)
        )

    @property
    def validated(self):
        try:
            validate(self)
            return True
        except TypeError:
            return False
