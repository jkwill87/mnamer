# coding=utf-8

from distutils.core import setup

with open('requirements.txt', 'r') as fp:
    REQUIREMENTS = fp.read().splitlines()

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
    license='MIT',
    long_description=LONG_DESCRIPTION,
    name='mnamer',
    packages=['mnamer'],
    install_requires=REQUIREMENTS,
    url='https://github.com/jkwill87/mnamer',
    version='0.2'
)
