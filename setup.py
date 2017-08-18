#!/usr/bin/env python3

"""setuptools for mnamer
"""

from setuptools import setup
from codecs import open
from os import path

# Get the long description from the README file
here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'readme.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(

    name='mnamer',
    version='2016.10',
    description='Automated movie file organizer',
    long_description=long_description,
    url='https://github.com/jkwill87/mnamer',
    author='Jessy Williams (jkwill87)',
    author_email='jessy@jessywilliams.com',
    license='MIT',
    packages=['mnamer'],

    entry_points={
        'console_scripts': [
            'mnamer = mnamer.__main__:main',
        ],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: MIT License',
        'Topic :: Utilities',
        'Topic :: Multimedia',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],

    install_requires=['requests', 'guessit']
)
