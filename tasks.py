#!/usr/bin/env python
# Jessy Williams (jessy@jessywilliams.com) 2018

from __future__ import print_function

from builtins import input
from os import system as sh, getcwd, sep
from sys import argv

PROJECT = getcwd().split(sep)[-1].lower()
VERSION = 0
VERSION_PATH = "%s/%s" % (PROJECT, '__version__.py')

try:
    # Load VERSION from __version__.py
    exec(open(VERSION_PATH).read(), globals())
except (IOError, TypeError):
    print('Could not determine version!')
    exit()


def help():
    print("usage: ./tasks.py " + '|'.join(sorted(_get_available_tasks())))


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


def bump_major():
    _bump(1.0)


def bump_minor():
    _bump(0.1)


def install():
    sh('pip install -q .')


def install_deps():
    sh('pip install -q -U requirements-dev.txt')


def uninstall():
    sh('sudo -H pip -q uninstall -y %s' % PROJECT)


def test():
    sh('coverage run --source=%s -m unittest tests/*.py -v' % PROJECT)


def version():
    print('%s %s' % (PROJECT, VERSION))
    sh('python --version')


def _bump(increment):
    new_version = "%0.1f" % (VERSION + increment)
    response = input('Bump from %s to %s? (y/n) ' % (VERSION, new_version))
    if not response.lower().strip().startswith('y'):
        print('aborting')
        return
    install_deps()

    with open(VERSION_PATH, 'w') as version_txt:
        version_txt.write('VERSION = %s\n' % new_version)
    sh('git reset HEAD -- .')  # unstage all changes
    sh('git add %s/__version__.py' % PROJECT)
    sh('git commit -m "Version bump"')
    sh('git tag %s' % new_version)
    sh('git push')
    sh('git push --tags')
    sh('./setup.py sdist bdist_wheel')
    sh('python -m twine upload dist/%s-%s*' % (PROJECT, new_version))
    clean()


def _get_available_tasks():
    def _fx(): pass

    return {
        f.__name__: f for f in globals().values()
        if type(f) == type(_fx) and f.__name__[0] != '_'
    }


# Program entry point
if __name__ == '__main__':
    tasks = {
        task_fn for task_name, task_fn in _get_available_tasks().items()
        if task_name in argv[1:]
    }
    if tasks: [task() for task in tasks]
    else: help()
