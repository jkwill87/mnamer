from sys import platform as _platform, version_info as _version_info

CONFIG_DEFAULTS = {

    # General Options
    'batch': False,
    'blacklist': (
        '.*sample.*',
        '^RARBG.*'
    ),
    'extension_mask': (
        'avi',
        'm4v',
        'mp4',
        'mkv',
        'ts',
        'wmv',
    ),
    'max_hits': 15,
    'recurse': False,
    'replacements': {
        '&': 'and',
        '@': 'at',
        ':': ',',
        ';': ','
    },
    'scene': False,
    'verbose': False,

    # Movie related
    'movie_api': 'tmdb',
    'movie_destination': '',
    'movie_template': (
        '<$title >'
        '<($year)>'
        '<$extension>'
    ),

    # Television related
    'television_api': 'tvdb',
    'television_destination': '',
    'television_template': (
        '<$series - >'
        '< - S$season>'
        '<E$episode - >'
        '< - $title>'
        '<$extension>'
    ),

    # API Keys -- consider using your own or IMDb if limits are hit
    'api_key_tmdb': 'db972a607f2760bb19ff8bb34074b4c7',
    'api_key_tvdb': 'E69C7A2CEF2F3152'
}

IS_PY2 = _version_info[0] == 2

IS_WINDOWS = _platform.startswith('win')

VERSION = 1.2
