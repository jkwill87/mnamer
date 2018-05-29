#!/usr/bin/env python
# Jessy Williams (jessy@jessywilliams.com) 2018

from __future__ import print_function
from builtins import input
from os import system as sh, getcwd, sep
from sys import argv

PROJECT = getcwd().split(sep)[-1].lower()
VERSION = 0

try:
    # Load VERSION from __version__.py
    exec(open("%s/%s" % (PROJECT, '__version__.py')).read(), globals())
except (IOError, TypeError):
    print('Could not determine version!')
    exit()


def help():
    print("usage: ./tasks.py " + '|'.join(sorted(TASKS)))


def clean():
    garbage = [
        '__pycache__',
        '.pyc',
        '.sqlite',
        '*egg-info',
        'build',
        'dist'
    ]
    sh('rm -rvf %s' % ' '.join(garbage))


def _bump(increment):
    new_version = VERSION + increment
    response = input('Bump from %s to %s? (y/n) ' % (VERSION, new_version))
    if not response.lower().strip().startswith('y'):
        print('aborting')
        return
    sh('pip install -q -r requirements-dev.txt')
    with open('version.txt', 'w') as version_txt:
        version_txt.write(str(new_version))
    sh('git commit -am "Minor version bump"')
    sh('git tag %s' % new_version)
    sh('git push --tags')
    sh('./setup.py sdist bdist_wheel')
    sh('python -m twine upload dis/%s-%s*.whl' % (PROJECT, new_version))
    sh('rm -r *.egg-info')


def bump_major():
    _bump(1.0)


def bump_minor():
    _bump(0.1)


def install():
    sh('pip install -q .')


def uninstall():
    sh('sudo -H pip -q uninstall -y mapi')


def test():
    sh('python -m unittest discover -v')


def version():
    print('%s version %s ' % (PROJECT, VERSION))


# Determine available tasks (e.g. defined function not prefixed by an underscore)
def _fx(): pass


TASKS = {
    f.__name__: f for f in globals().values() 
    if type(f) == type(_fx) and f.__name__[0] != '_'
}

# Determine arguments
task_name = argv[1] if len(argv) == 2 else None

# Run task (defaulting to help in undefined)
TASKS.get(task_name, help)()
