
import logging.config
from sys import modules

__all__ = [
    'M_AVAIL_API_ALL',
    'M_AVAIL_API_MOVIE',
    'M_AVAIL_API_TV',
    'M_TEMPLATE_TV',
    'M_TEMPLATE_MOVIE'
]

# Setup logging; automatically set DEBUG-level if running in debug mode
logging.basicConfig(
    level=logging.DEBUG if 'pydevd' in modules else 100,
    format='%(levelname)s:%(name)s.%(funcName)s - %(message)s'
)

# Constant Values
M_AVAIL_API_TV = {'omdb', 'tvdb'}
M_AVAIL_API_MOVIE = {'omdb', 'imdb'}
M_AVAIL_API_ALL = M_AVAIL_API_TV | M_AVAIL_API_MOVIE
M_TEMPLATE_TV = '<[series]/><[series] - ><[airdate]><[season]x><[episode]>< - [title]>'
M_TEMPLATE_MOVIE = '<[title] ><([year])>/<[title] ><([year])>'
M_MOVIE = 'movie'
M_TELEVISION = 'television'
