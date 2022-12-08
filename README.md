[![PyPI](https://img.shields.io/pypi/v/mnamer.svg?style=for-the-badge)](https://pypi.python.org/pypi/mnamer)
[![Tests](https://img.shields.io/github/workflow/status/jkwill87/mnamer/push?style=for-the-badge&label=Tests)](https://img.shields.io/github/actions/workflow/status/jkwill87/mnamer/.github/workflows/push.yml?branch=main)
[![Coverage](https://img.shields.io/codecov/c/github/jkwill87/mnamer/main.svg?style=for-the-badge)](https://codecov.io/gh/jkwill87/mnamer)
[![Licence](https://img.shields.io/github/license/jkwill87/mnamer.svg?style=for-the-badge)](https://en.wikipedia.org/wiki/MIT_License)
[![Style: Black](https://img.shields.io/badge/Style-Black-black.svg?style=for-the-badge)](https://github.com/ambv/black)

<img src="https://github.com/jkwill87/mnamer/raw/main/assets/logo.png" width="450"/>

# mnamer

mnamer (**m**edia re**namer**) is an intelligent and highly configurable media organization utility. It parses media filenames for metadata, searches the web to fill in the blanks, and then renames and moves them.

Currently it has integration support with [TVDb](https://thetvdb.com) and [TvMaze](https://www.tvmaze.com) for television episodes and [TMDb](https://www.themoviedb.org/) and [OMDb](https://www.omdbapi.com) for movies.

<img src="https://github.com/jkwill87/mnamer/raw/main/assets/screenshot.png" width="750"/>

## Documentation

Check out the [wiki page](https://github.com/jkwill87/mnamer/wiki) for more details.

💾 [**Installation**](https://github.com/jkwill87/mnamer/wiki/Installation)

`$ pip3 install --user mnamer`

🤖 [**Automation**](https://github.com/jkwill87/mnamer/wiki/Automation)

`$ docker pull jkwill87/mnamer`

✍️ [**Formatting**](https://github.com/jkwill87/mnamer/wiki/Formatting)

Using the **episode-directory**, **episode-format**, **movie-directory**, or **movie-format** settings you customize how your files are renamed. Variables wrapped in braces `{}` get substituted with of parsed values of template field variables.

🌐 [**Internationalization**](https://github.com/jkwill87/mnamer/wiki/Internationalization)

Language is supported by the default TMDb and TVDb providers. You can use the `--language` setting to set the language used for templating.

mnamer also supports subtitle files (.srt, .idx, .sub). It will use the format pattern used for movie or episode media files with its extension prefixed by its 2-letter language code.

🧰 [**Settings**](https://github.com/jkwill87/mnamer/wiki/Settings)

```
USAGE: mnamer [preferences] [directives] target [targets ...]

POSITIONAL:
  [TARGET,...]: media file file path(s) to process

PARAMETERS:
  The following flags can be used to customize mnamer's behaviour. Their long
  forms may also be set in a '.mnamer-v2.json' config file, in which case cli
  arguments will take precedence.

  -b, --batch: process automatically without interactive prompts
  -l, --lower: rename files using lowercase characters
  -r, --recurse: search for files within nested directories
  -s, --scene: use dots in place of alphanumeric chars
  -v, --verbose: increase output verbosity
  --hits=<NUMBER>: limit the maximum number of hits for each query
  --ignore=<PATTERN,...>: ignore files matching these regular expressions
  --language=<LANG>: specify the search language
  --mask=<EXTENSION,...>: only process given file types
  --no-guess: disable best guess; e.g. when no matches or network down
  --no-overwrite: prevent relocation if it would overwrite a file
  --no-style: print to stdout without using colour or unicode chars
  --movie-api={*tmdb,omdb}: set movie api provider
  --movie-directory: set movie relocation directory
  --movie-format: set movie renaming format specification
  --episode-api={tvdb,*tvmaze}: set episode api provider
  --episode-directory: set episode relocation directory
  --episode-format: set episode renaming format specification

DIRECTIVES:
  Directives are one-off arguments that are used to perform secondary tasks
  like overriding media detection. They can't be used in '.mnamer-v2.json'.

  -V, --version: display the running mnamer version number
  --clear-cache: clear request cache
  --config-dump: prints current config JSON to stdout then exits
  --config-ignore: skips loading config file for session
  --config-path=<PATH>: specifies configuration path to load
  --id-imdb=<ID>: specify an IMDb movie id override
  --id-tmdb=<ID>: specify a TMDb movie id override
  --id-tvdb=<ID>: specify a TVDb series id override
  --id-tvmaze=<ID>: specify a TvMaze series id override
  --no-cache: disable request cache
  --media={movie,episode}: override media detection
  --test: mocks the renaming and moving of files
```

Parameters can either by entered as command line arguments or from a config file named `.mnamer-v2.json`.

## Contributions

Community contributions are a welcome addition to the project. In order to be merged upsteam any additions will need to be formatted with [black](https://black.readthedocs.io) for consistency with the rest of the project and pass the continuous integration tests run against each PR. Before introducing any major features or changes to the configuration api please consider opening [an issue](https://github.com/jkwill87/mnamer/issues) to outline your proposal.

Bug reports are also welcome on the [issue page](https://github.com/jkwill87/mnamer/issues). Please include any generated crash reports if applicable. Feature requests are welcome but consider checking out [if it is in the works](https://github.com/jkwill87/mnamer/issues?q=label%3Arequest) first to avoid duplication.
