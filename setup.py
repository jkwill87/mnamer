#!/usr/bin/env python
# coding=utf-8

from sys import version_info, platform

from setuptools import setup

from mnamer.__version__ import VERSION

IS_PY2 = version_info[0] == 2
IS_WINDOWS = platform.startswith('win')

with open('readme.md', 'r') as fp:
    LONG_DESCRIPTION = fp.read()

requirements = [
    'appdirs>=1.4',
    'guessit>=2.1',
    'mapi==3.1.1',
    'termcolor>=1'
]

if IS_WINDOWS:
    requirements.append('colorama>=0.3.9')

if IS_PY2:
    requirements.append('future>=0.16')

setup(
    author='Jessy Williams',
    author_email='jessy@jessywilliams.com',
    description='A media file organiser',
    entry_points={
        'console_scripts': [
            'mnamer=mnamer.__main__:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    name='mnamer',
    packages=['mnamer'],
    url='https://github.com/jkwill87/mnamer',
    version=VERSION
)
