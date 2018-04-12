#!/usr/bin/env python
# coding=utf-8

from distutils.core import setup

with open('readme.rst', 'r') as fp:
    LONG_DESCRIPTION = fp.read()

setup(
    author='Jessy Williams',
    author_email='jessy@jessywilliams.com',
    description='A media file organiser',
    entry_points={
        'console_scripts': [
            'mnamer=mnamer.__main__:main'
        ]
    },
    install_requires=[
        'appdirs>=1.4',
        'guessit>=2.1',
        'mapi==3.0.1',
        'termcolor>=1',
        'future>=0.16;python_version<"3"',
        'pathlib>=1;python_version<"3"'
    ],
    license='MIT',
    long_description=LONG_DESCRIPTION,
    name='mnamer',
    packages=['mnamer'],
    python_requires='>=3.5',
    url='https://github.com/jkwill87/mnamer',
    version='1.2'
)
