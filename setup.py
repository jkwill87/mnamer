# coding=utf-8

from distutils.core import setup

with open('requirements.txt', 'r') as fp:
    REQUIREMENTS = fp.read().splitlines()

with open('readme.rst', 'r') as fp:
    LONG_DESCRIPTION = fp.read()

ABOUT = {
    'author': 'Jessy Williams',
    'author_email': 'jessy@jessywilliams.com',
    'description': 'A media file organiser',
    'license': 'MIT',
    'long_description': LONG_DESCRIPTION,
    'name': 'mnamer',
    'packages': ['mnamer'],
    'install_requires': REQUIREMENTS,
    'url': 'https://github.com/jkwill87/mnamer',
    'version': '0.1'
}

setup(**ABOUT)
