[![pypi](https://img.shields.io/pypi/v/mnamer.svg?style=for-the-badge)](https://pypi.python.org/pypi/mnamer)
[![travis\_ci](https://img.shields.io/travis/jkwill87/mnamer/develop.svg?style=for-the-badge)](https://travis-ci.org/jkwill87/mnamer)
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


| Preference              | Arguments        | Description                                           |
|:------------------------|:-----------------|:------------------------------------------------------|
|-b, --batch              |                  | batch mode; disables interactive prompts              |
|-s, --scene              |                  | scene mode; replace non ascii-alphanumerics with `.`  |
|-r, --recurse            |                  | show this help message and exit                       |
|-v, --verbose            |                  | increases output verbosity                            |
|--blacklist              | pattern          | ignore files including these words                     |
|--hits                   | number           | limits the maximum number of hits for each query      |
|--extmask                | extention(s)     | define the extension mask used by the the file parser   |
|--nocache                |                  | disables and clears result cache                      |
|--nostyle                |                  | disables colours and uses ASCII chars for UI prompts  |
|--movie_api              | `imdb` or `tmdb` | set movie api provider                                |
|--movie_directory        | path             | set movie relocation directory                        |
|--movie_template         | template         | set movie renaming template                           |
|--television_api         | `tvdb`           | set television api provider                           |
|--television_directory   | path             | set television relocation directory                   |
|--television_template    | template         | set television renaming template                      |


# Directives

Whereas preferences configure how mnamer works, directives are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

| Option           | Arguments               | Description                              |
|:-----------------|:------------------------|:-----------------------------------------|
| --config         | path                    | prints config JSON to stdout then exits  |
| --id             | id                      | explicitly specify movie or series id    |
| --media          | `movie` or `television` | override media detection                 |
| --test           |                         | mocks the renaming and moving of files   |


# Templating


You have complete control of how media files are renamed using mnamer's template options:

- you can use templating with the following options: **television_directory**, **television_template**, **movie_directory**, **movie_template**
- metadata fields prefixed with a sigil `$` found inside angle brackets with the result of a match
- any leading or trailing whitespace will be trimmed
- if a field can't be matched, the entire contents of the bracket are disregared


## Examples
<details>
<summary>SxE Episodes Format</summary>

- television_template: `<$series - >< - $seasonx><$episode - >< - $title><$extension>`
- target: `~/Downloads/Rick.and.Morty.S02E01.WEBRip.x264-RARBG.mp4`
- result: `~/Downloads/Rick and Morty - 02x01 - A Rickle in Time.mp4`
</details>


<details>
<summary>Missing Metadata</summary>

*Note: Target file is missing group metadata field in title and will be omitted gracefully*

- television_template: `<$series - >< - S$season><E$episode - >< - $group - >< - $title><$extension>`
- target: `~/Downloads/The.Orville.S01E01.1080p.WEB-DL.DD5.1.H264-RARBG.mkv`
- result: `~/Downloads/The Orville - S01E01 - Old Wounds.mkv`
</details>

<details>
<summary>Subdirectories</summary>

*Note: If the subdirectory doesn't exist, mnamer will create it*

- movie_template: `<$title ><($year)><$extension>`
- movie_directory: `/media/movies/<$title ><($year)>`
- target: `~/Downloads/The.Goonies.1985.720p.BluRay.x264-SiNNERS.mkv`
- result: `/media/movies/The Goonies (1985)/The Goonies (1985).mkv`
</details>


# Metadata Fields

| Field   | Description                      |
|:--------|:---------------------------------|
| title   | movie or episode title           |
| year    | movie release year               |
| series  | tv series' name                  |
| season  | tv series' airing season number  |
| episode | tv series' airing episode number |
