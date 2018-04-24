[![licence](https://img.shields.io/github/license/jkwill87/mnamer.svg)](https://en.wikipedia.org/wiki/MIT_License)
[![pypi](https://img.shields.io/pypi/v/mnamer.svg)](https://pypi.python.org/pypi/mnamer)

![manmer logo](_assets/mnamer.png)

# mnamer

mnamer (**m**edia re**namer**) is an intelligent and highly configurable media organization utility. It parses media filenames for metadata, searches the web to fill in the blanks, and then renames and moves them.


# installation

`$ [sudo -H] pip install mnamer`


# Usage

`mnamer target [targets ...] [options] [directives]`


# Options

mnamer attempts to load options from mnamer.json in the user's configuration directory, .mnamer.json in the current working directory, and then from the command line-- overriding each other also in that order.


| Option                  | Arguments        | Description                                                 |
|:------------------------|:-----------------|:------------------------------------------------------------|
|-b, --batch              |                  | batch mode; disables interactive prompts                    |
|-s, --scene              |                  | scene mode; replace whitespace, non-ascii characters w/ `.` |
|-r, --recurse            |                  | show this help message and exit                             |
|-v, --verbose            |                  | increases output verbosity                                  |
|--blacklist              | pattern          | ignore files including these words                          |
|--max_hits               | number           | limits the maximum number of hits for each query            |
|--extension_mask         | extention(s)     | define the extension mask used by the the file parser       |
|--movie_api              | `imdb` or `tmdb` | set movie api provider                                      |
|--movie_destination      | path             | set movie relocation destination                            |
|--movie_template         | template         | set movie renaming template                                 |
|--television_api         | `tvdb`           | set television api provider                                 |
|--television_destination | path             | set television relocation destination                       |
|--television_template    | template         | set television renaming template                            |


# Directives

Whereas options configure how mnamer works, directives are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

| Option           | Arguments               | Description                                          |
|:-----------------|:------------------------|:-----------------------------------------------------|
| --config_load    | path                    | import configuration from file                       |
| --config_save    | path                    | save configuration to file                           |
| --id             | id                      | explicitly specify movie or series id                |
| --media          | `movie` or `television` | override media detection; either movie or television |
| --test_run       |                         | mocks the renaming and moving of files               |


# Configuration Files

In addition to the option argument flags listed above, mnamer can also be configured via JSON configuration file(s). These are loaded and applied from the following locations, in the following order:

1. As **.mnamer.json** within the current working directory (e.g. *./.mnamer.json*)
2. As **mnamer.json** from within the user config directory (e.g. *~/.config/mnamer.json*)
3. As **.mnamer.json** from the user home directory (e.g. *~/.mnamer.json*)
4. Any path explicitly passed using the `--load_config` directive


# Templating


You have complete control of how media files are renamed using mnamer's template options:

- you can use templating with the following options: **television_destination**, **television_template**, **movie_destination**, **movie_template**
- metadata fields prefixed with a sigil `$` found inside angle brackets with the result of a match
- any leading or trailing whitespace will be trimmed
- if a field can't be matched, the entire contents of the bracket are disregared


## Example: SxE Episodes Format

- television_template: `<$series - >< - $seasonx><$episode - >< - $title><$extension>`
- target: `~/Downloads/Rick.and.Morty.S02E01.WEBRip.x264-RARBG.mp4`
- result: `~/Downloads/Rick and Morty - 02x01 - A Rickle in Time.mp4`


## Example: Missing Metadata


*Note: Target file is missing group metadata field in title and will be omitted gracefully*

- television_template: `<$series - >< - S$season><E$episode - >< - $group - >< - $title><$extension>`
- target: `~/Downloads/The.Orville.S01E01.1080p.WEB-DL.DD5.1.H264-RARBG.mkv`
- result: `~/Downloads/The Orville - S01E01 - Old Wounds.mkv`


## Example: Subdirectories

*Note: If the subdirectory doesn't exist, mnamer will create it*

- movie_template: `<$title ><($year)><$extension>`
- movie_destination: `/media/movies/<$title ><($year)>`
- target: `~/Downloads/The.Goonies.1985.720p.BluRay.x264-SiNNERS.mkv`
- result: `/media/movies/The Goonies (1985)/The Goonies (1985).mkv`


# Metadata Fields

| Field   | Description                      |
|:--------|:---------------------------------|
| title   | movie or episode title           |
| year    | movie release year               |
| series  | tv series' name                  |
| season  | tv series' airing season number  |
| episode | tv series' airing episode number |
