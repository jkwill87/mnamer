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

mnamer v2 is under development. It is currently in a functional state and suitable for use so long as unit tests are passing. This version currently introduces breaking changes from v1 and has the potential to continue doing so. These changes will be documented upon release.

`$ pip install -U https://github.com/jkwill87/mnamer/archive/develop.zip`

## Notes

If you want to install it using system python (e.g. the one that comes with your OS, not really recommended) and get a permission error you need to use either `sudo -H pip ...` or `pip install --user ...`.


# Usage

`mnamer target [targets ...] [preferences] [directives]`


# Preferences

mnamer attempts to load preferences from .mnamer.json in the user's home directory, the current working directory, and then in each directory up the drive towards the drive root (e.g. `C:/`, `/`).

| Preference             | Arguments        | Description                                                     |
| :--------------------- | :--------------- | :-------------------------------------------------------------- |
| -b, --batch            |                  | batch mode; disable interactive prompts                         |
| -l, --lowercase        |                  | rename filenames as lowercase                                   |
| -r, --recurse          |                  | show this help message and exit                                 |
| -s, --scene            |                  | scene mode; replace non ascii-alphanumerics with `.`            |
| -v, --verbose          |                  | increase output verbosity                                       |
| --nocache              |                  | disable and clear result cache                                  |
| --noguess              |                  | disable best guess fallback; e.g. when no matches, network down |
| --nostyle              |                  | disable colours and uses ASCII chars for UI prompts             |
| --blacklist            | pattern          | ignore files including these words                              |
| --extmask              | extention(s)     | define the extension mask used by the the file parser           |
| --hits                 | number           | limit the maximum number of hits for each query                 |
| --movie_api            | `imdb` or `tmdb` | set movie api provider                                          |
| --movie_directory      | path             | set movie relocation directory                                  |
| --movie_format         | format           | set movie renaming format                                       |
| --television_api       | `tvdb`           | set television api provider                                     |
| --television_directory | path             | set television relocation directory                             |
| --television_format    | format           | set television renaming format                                  |

**Protip:** Quickly save your current preference set on MacOS or *nix by running `mnamer --config > ~/.mnamer.conf`.


# Directives

Whereas preferences configure how mnamer works, directives are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

| Option          | Arguments               | Description                             |
| :-------------- | :---------------------- | :-------------------------------------- |
| --config_dump   |                         | prints config JSON to stdout then exits |
| --config_ignore |                         | skips loading config file for session   |
| --id            | id                      | explicitly specify movie or series id   |
| --media         | `movie` or `television` | override media detection                |
| --test          |                         | mocks the renaming and moving of files  |


# Formatting

You have complete control of how media files are renamed using mnamer's format options:

- you can use formatting with the following options: **television_directory**, **television_format**, **movie_directory**, **movie_format**
- uses Python's [format string syntax](https://docs.python.org/3/library/string.html#format-string-syntax) specification for to replace metadata fields
- essentially just replaces variables in curly braces with metadata fields
- automatically trims results, concatenates whitespace, and removes empty brackets

## Examples

<details>
<summary>00x00 Television Format</summary>

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
