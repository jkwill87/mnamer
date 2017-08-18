import configparser
import sys
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import List

from mnamer.metadata import MediaType


class API(Enum):
    IMDB = 'IMDb'
    TVDB = 'TVDb'
    RT = 'RT'
    OMDB = 'OMDb'


class InvalidSectionError(configparser.Error):
    """Raised when..."""

    def __init__(self, section):
        configparser.Error.__init__(self, f'No section: {section}')
        self.section = section


class InvalidOptionError(configparser.Error):
    """Raised when..."""

    def __init__(self, option):
        configparser.Error.__init__(self, f'No option: {option}')
        self.option = option


class InvalidValueError(configparser.Error):
    """Raised when..."""

    def __init__(self, value):
        configparser.Error.__init__(self, f'Invalid Svalue: {value}')


class Config(configparser.ConfigParser):
    """Used to store and validate mnamer's configuration options.
    """

    _SECTION_PREFERENCES = OrderedDict((
        ('recurse', False),
        ('batch', False),
        # ('colour', True),
        ('dots', False),
        ('lower', False),
        ('extmask', "avi,m4v,mp4,mkv,ts,wmv"),
    ))

    _SECTION_MOVIE = OrderedDict((
        ('api', "imdb"),
        ('template', "@title (@year)/@title (@year)"),
        ('destination', '')
    ))

    _SECTION_TELEVISION = OrderedDict((
        ('api', "tvdb"),
        ('template', "@show/@show - @seasonx@episode - @title"),
        ('destination', '')
    ))

    _SECTION_API_KEYS = OrderedDict((
        ('tvdb', ''),
        ('omdb', ''),
        ('rt', '')
    ))

    _CONFIG_DEFAULTS = OrderedDict((
        ('preferences', _SECTION_PREFERENCES),
        ('apikeys', _SECTION_API_KEYS),
        ('movie', _SECTION_MOVIE),
        ('television', _SECTION_TELEVISION)
    ))

    USER_HOME = Path.home()

    def __init__(self, addtl_path: str = ''):
        super().__init__()
        config_paths = ['.mnamer.cfg', str(self.USER_HOME) + '/.mnamer.cfg']
        if addtl_path:
            config_paths += addtl_path

        # Load default configuration values
        self.read_dict(self._CONFIG_DEFAULTS)
        self.read(config_paths)
        self.validate()

    def api(self, mtype: MediaType):
        if self.has_option(mtype.value, 'api'):
            return {
                'imdb': API.IMDB,
                'tvdb': API.TVDB,
                'rt': API.RT,
                'omdb': API.OMDB,
            }.get(self[mtype.value]['api'].lower(), None)
        else:
            return None

    @property
    def batch(self) -> bool:
        return self.getboolean('preferences', 'batch')

    @batch.setter
    def batch(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError
        else:
            self.set('preferences', 'batch', str(value))

    @property
    def colour(self) -> bool:
        return self.getboolean('preferences', 'colour')

    @colour.setter
    def colour(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError
        else:
            self.set('preferences', 'colour', str(value))

    @property
    def tvdest(self) -> str:
        return self.get('television', 'destination')

    @tvdest.setter
    def tvdest(self, value):
        if value:
            if Path(value).exists():
                self.set('television', 'destination', value)
            else:
                raise FileNotFoundError
        else:
            self.set('television', 'destination', '')

    @property
    def tvtemplate(self) -> str:
        return self.get('television', 'template')

    @tvtemplate.setter
    def tvtemplate(self, value: str):
        if not isinstance(value, str):
            raise TypeError
        elif '@' not in value:
            raise InvalidValueError(value)
        else:
            self.set('television', 'template', value)

    @property
    def dots(self) -> bool:
        return self.getboolean('preferences', 'dots')

    @dots.setter
    def dots(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError
        else:
            self.set('preferences', 'dots', str(value))

    @property
    def extmask(self) -> List[str]:
        return list(
            ext.strip() for ext in self['preferences']['extmask'].split(','))

    @extmask.setter
    def extmask(self, value_list: list):
        values = ",".join([str(item) for item in value_list])
        self.set('preferences', 'extmask', values)

    @property
    def lower(self) -> bool:
        return self.getboolean('preferences', 'lower')

    @lower.setter
    def lower(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError
        else:
            self.set('preferences', 'lower', str(value))

    @property
    def moviedest(self):
        return self.get('movie', 'destination')

    @moviedest.setter
    def moviedest(self, value):
        if value:
            if Path(value).exists():
                self.set('movie', 'destination', value)
            else:
                raise FileNotFoundError
        else:
            self.set('movie', 'destination', '')

    @property
    def movietemplate(self):
        return self.get('movie', 'template')

    @movietemplate.setter
    def movietemplate(self, value: str):
        if not isinstance(value, str):
            raise TypeError
        elif '@' not in value:
            raise InvalidValueError(value)
        else:
            self.set('movie', 'template', value)

    @property
    def recurse(self) -> bool:
        return self.getboolean('preferences', 'recurse')

    @recurse.setter
    def recurse(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError
        else:
            self.set('preferences', 'recurse', str(value))

    def write_file(self, path='') -> None:
        if path:
            with open(path, 'w') as configfile:
                self.write(configfile)
        else:
            self.write(sys.stdout)

    def format(self, mtype: MediaType) -> str:
        return self[mtype.value]['format']

    def validate(self) -> None:

        for section in self.sections():

            # Validate Sections
            if section not in self._CONFIG_DEFAULTS.keys():
                raise InvalidSectionError(section)

                # for section in (self._CONFIG_DEFAULTS.keys()):
                #     invalid_options += [
                #         section + '->' + option for option in
                #         self.options(section) if
                #         option not in self._CONFIG_DEFAULTS[section].keys()
                #         ]
                #
                # pprint(invalid_sections)
                # pprint(invalid_options)
