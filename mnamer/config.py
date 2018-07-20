from copy import deepcopy

from attr import attrib, attrs, validate, validators

from mnamer.args import Arguments
from mnamer.exceptions import MnamerConfigException
from mnamer.utils import config_find, config_load, merge_dicts


@attrs
class Config:
    batch = attrib()
    blacklist = attrib()
    extmask = attrib()
    hits = attrib()
    recurse = attrib()
    scene = attrib()
    verbose = attrib()
    movie_api = attrib()
    movie_destination = attrib()
    movie_template = attrib()
    television_api = attrib()
    televsion_destination = attrib()
    television_template = attrib()

    def __init__(self, load_file=True):
        self._data = deepcopy(Arguments.config)
        self._load_error = None
        self._loaded_file = None

    def load_file(self):
        try:
            json_file = config_find()
            json_data = config_load(json_file)
            self._data = merge_dicts(self._data, json_data)
            self._loaded_file = json_file
        except MnamerConfigException as e:
            self._load_error = e

    @property
    def loaded_file(self):
        return self._loaded_file

    @property
    def load_error(self):
        return self._load_error

    @property
    def validated(self):
        try:
            validate(self)
            return True
        except TypeError:
            return False
