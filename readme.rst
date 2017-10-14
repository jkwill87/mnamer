|licence| |pypi|


mnamer
======

.. image:: _images/mnamer.png

mnamer (**m**\ edia re\ **namer**) is an intelligent and highly configurable media organization utility. It parses media filenames for metadata, searches the web to fill in the blanks, and then renames and moves them.


Installation
============

``$ pip3 install mnamer``


Usage
=====

``mnamer target [targets ...] [options] [directives]``


Options
-------

mnamer attempts to load options from ``mnamer.json`` in the user's configuration directory, ``.mnamer.json`` in the current working directory, and then from the command line-- overriding each other also in that order.

- **-b, --batch**: batch mode; disables interactive prompts
- **-d, --dots**: format using dots in place of whitespace when renaming
- **-d, --lower**: format using lowercase when renaming
- **-r, --recurse**: show this help message and exit
- **-v, --verbose**: increases output verbosity

- **--max_hits < number >**: limits the maximum number of hits for each query
- **--extension_mask < ext, ext, ... >**: define the extension mask used by the the file parser

- **--movie_api { imdb, tmdb }**: set movie api provider
- **--movie_destination < path >**: set movie relocation destination
- **--movie_template < template >**: set movie renaming template

- **--television_api { tvdb }**: set television api provider
- **--television_destination < path >**: set television relocation destination
- **--television_template < template >**: set television renaming template


Directives
----------

Whereas options configure how mnamer works, directives are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

- **--config_load < path >**: import configuration from file
- **--config_save < path >**: save configuration to file

- **--id < id >**: explicitly specify movie or series id
- **--media { movie, television }**: override media detection; either movie or television

- **--test_run**: set movie api provider


More Information
----------------

`Check out the project wiki <https://github.com/jkwill87/mnamer/wiki>`_ for examples, use cases, help, and more!


License
=======

MIT. See license.txt for details.

.. |licence| image:: https://img.shields.io/github/license/jkwill87/mnamer.svg
   :target: https://en.wikipedia.org/wiki/MIT_License
.. |pypi| image:: https://img.shields.io/pypi/v/mnamer.svg
   :target: https://pypi.python.org/pypi/mnamer
