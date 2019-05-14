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

## Stable Version

`$ pip install mnamer`

## Development Version

`$ pip install https://github.com/jkwill87/mnamer/archive/develop.zip`

## Notes

If you want to install it using system python (e.g. the one that comes with your OS, not really recommended) and get a permission error you need to use either `sudo -H pip ...` or `pip install --user ...`.


# Usage

`mnamer target [targets ...] [preferences] [directives]`


# Preferences

mnamer attempts to load preferences from .mnamer.json in the user's home directory, the current working directory, and then in each directory up the drive towards the drive root (e.g. `C:/`, `/`).

| Preference             | Arguments        | Description                                           |
| :--------------------- | :--------------- | :---------------------------------------------------- |
| -b, --batch            |                  | batch mode; disables interactive prompts              |
| -s, --scene            |                  | scene mode; replace non ascii-alphanumerics with `.`  |
| -r, --recurse          |                  | show this help message and exit                       |
| -v, --verbose          |                  | increases output verbosity                            |
| --blacklist            | pattern          | ignore files including these words                    |
| --hits                 | number           | limits the maximum number of hits for each query      |
| --extmask              | extention(s)     | define the extension mask used by the the file parser |
| --nocache              |                  | disables and clears result cache                      |
| --nostyle              |                  | disables colours and uses ASCII chars for UI prompts  |
| --movie_api            | `imdb` or `tmdb` | set movie api provider                                |
| --movie_directory      | path             | set movie relocation directory                        |
| --movie_format         | format         | set movie renaming format                           |
| --television_api       | `tvdb`           | set television api provider                           |
| --television_directory | path             | set television relocation directory                   |
| --television_format    | format         | set television renaming format                      |


# Directives

Whereas preferences configure how mnamer works, directives are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

| Option   | Arguments               | Description                             |
| :------- | :---------------------- | :-------------------------------------- |
| --config | path                    | prints config JSON to stdout then exits |
| --id     | id                      | explicitly specify movie or series id   |
| --media  | `movie` or `television` | override media detection                |
| --test   |                         | mocks the renaming and moving of files  |


# Formatting

You have complete control of how media files are renamed using mnamer's format options:

- you can use formatting with the following options: **television_directory**, **television_format**, **movie_directory**, **movie_format**
- uses Python's [format string syntax](https://docs.python.org/3/library/string.html#format-string-syntax) specification for to replace metadata fields
- essentially just replaces variables in curly braces with metadata fields
- automatically trims results, concatenates whitespace, and removes empty brackets 

## Examples

<details>
<summary>S00xE00 Episodes Format</summary>

- television_format: `{series} {season:02}x{episode:02}{title}{extension}`
- target: `~/Downloads/Rick.and.Morty.S02E01.WEBRip.x264-RARBG.mp4`
- result: `~/Downloads/Rick and Morty - 02x01 - A Rickle in Time.mp4`
  </details>

<details>
<summary>Missing Metadata</summary>

_Note: Target file is missing group metadata field in title and will be omitted gracefully_

- television_format: `{series} - S{season:02}E{episode:02} - {group} - {title}{extension}`
- target: `~/Downloads/The.Orville.S01E01.1080p.WEB-DL.DD5.1.H264.mkv`
- result: `~/Downloads/The Orville - S01E01 - Old Wounds.mkv`
  </details>

<details>
<summary>Nesting Directories</summary>

_Note: If the subdirectory doesn't exist, mnamer will create it_

- movie_format: `{title} ({year}){extension}`
- movie_directory: `/media/movies/{title} ({year})`
- target: `~/Downloads/The.Goonies.1985.720p.BluRay.x264-SiNNERS.mkv`
- result: `/media/movies/The Goonies (1985)/The Goonies (1985).mkv`
  </details>


# Metadata Fields

| Field   | Description                      |
| :------ | :------------------------------- |
| title   | movie or episode title           |
| year    | movie release year               |
| series  | tv series' name                  |
| season  | tv series' airing season number  |
| episode | tv series' airing episode number |
