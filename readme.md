[![pypi](https://img.shields.io/pypi/v/mnamer.svg?style=for-the-badge)](https://pypi.python.org/pypi/mnamer)
[![travis_ci](https://img.shields.io/travis/jkwill87/mnamer/develop.svg?style=for-the-badge)](https://travis-ci.org/jkwill87/mnamer)
[![coverage](https://img.shields.io/codecov/c/github/jkwill87/mnamer/develop.svg?style=for-the-badge)](https://codecov.io/gh/jkwill87/mnamer)
[![licence](https://img.shields.io/github/license/jkwill87/mnamer.svg?style=for-the-badge)](https://en.wikipedia.org/wiki/MIT_License)
[![code style black](https://img.shields.io/badge/Code%20Style-Black-black.svg?style=for-the-badge)](https://github.com/ambv/black)

![mnamer logo](https://github.com/jkwill87/mnamer/raw/develop/_assets/logo.png)


# mnamer

mnamer (**m**edia re**namer**) is an intelligent and highly configurable media organization utility. It parses media filenames for metadata, searches the web to fill in the blanks, and then renames and moves them.

![demo](https://github.com/jkwill87/mnamer/blob/develop/_assets/demo.svg)


# Installation

**Protip**: If you want to install mnamer using system python (e.g. the one that comes with your OS, not really recommended) and get a permission error you need to use either `pip --user ...` or `sudo -H pip ...`.


## Stable Version

`$ pip install mnamer`

## Development Version

mnamer v2 is under development. It is currently in a functional state and suitable for use so long as unit tests are passing. This version currently introduces breaking configuration changes from v1 and has the potential to continue doing so. See [the Wiki Page](https://github.com/jkwill87/mnamer/wiki/Version-2-Changes) for a list of these changes.

`$ pip install -U https://github.com/jkwill87/mnamer/archive/develop.zip`


# Usage

`mnamer target [targets ...] [preferences] [directives]`


# Preferences

mnamer attempts to load preferences from .mnamer.json in the user's home directory, the current working directory, and then in each directory up the drive towards the drive root (e.g. `C:/`, `/`).

| Preference             | Arguments        | Description                                                     |
| :--------------------- | :--------------- | :-------------------------------------------------------------- |
| -b, --batch            |                  | batch mode; disable interactive prompts                         |
| -l, --lowercase        |                  | rename files using lowercase characters only                    |
| -r, --recurse          |                  | show this help message and exit                                 |
| -s, --scene            |                  | scene mode; replace non ascii-alphanumerics with `.`            |
| -v, --verbose          |                  | increase output verbosity                                       |
| --nocache              |                  | disable and clear result cache                                  |
| --noguess              |                  | disable best guess fallback; e.g. when no matches, network down |
| --nostyle              |                  | disable colours and uses ASCII characters for prompts           |
| --blacklist            | pattern          | ignore files including these words (regex)                      |
| --extensions           | extension(s)     | only process files with given extensions                        |
| --hits                 | number           | limit the maximum number of hits for each query                 |
| --movie-api            | `imdb` or `tmdb` | set movie api provider                                          |
| --movie-directory      | path             | set movie relocation directory                                  |
| --movie-format         | format           | set movie renaming format                                       |
| --television-api       | `tvdb`           | set television api provider                                     |
| --television-directory | path             | set television relocation directory                             |
| --television-format    | format           | set television renaming format                                  |

**Protip:** Quickly save your current preference set on MacOS or *nix by running `mnamer --config > ~/.mnamer.conf`.


# Directives

Whereas preferences configure how mnamer works, directives are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

| Option          | Arguments               | Description                             |
| :-------------- | :---------------------- | :-------------------------------------- |
| --config-dump   |                         | prints config JSON to stdout then exits |
| --config-ignore |                         | skips loading config file for session   |
| --id            | id                      | explicitly specify movie or series id   |
| --media-force   | `movie` or `television` | override media detection                |
| --media-mask    | `movie` or `television` | only process given media type           |
| --test          |                         | mocks the renaming and moving of files  |


# Formatting

You have complete control of how media files are renamed using mnamer's format options:

- you can use formatting with the following options: **television_directory**, **television_format**, **movie_directory**, **movie_format**
- uses Python's [format string syntax](https://docs.python.org/3/library/string.html#format-string-syntax) specification for to replace metadata fields
- essentially just replaces variables in curly braces with metadata fields
- automatically trims results, concatenates whitespace, and removes empty brackets
- nexted directories are automatically created

See [the Wiki Page](https://github.com/jkwill87/mnamer/wiki/Formatting-Examples) for examples.

# Metadata Fields

| Field   | Description                      |
| :------ | :------------------------------- |
| title   | movie or episode title           |
| year    | movie release year               |
| series  | tv series' name                  |
| season  | tv series' airing season number  |
| episode | tv series' airing episode number |
