PREFERENCE_KEYS = {
    "api_key_tmdb",
    "api_key_tvdb",
    "batch",
    "blacklist",
    "extmask",
    "hits",
    "movie_api",
    "movie_destination",
    "movie_template",
    "recurse",
    "replacements",
    "scene",
    "television_api",
    "television_destination",
    "television_template",
    "verbose",
}

DIRECTIVE_KEYS = {"help", "version", "media", "test", "id"}

USAGE = "mnamer target [targets ...] [options] [directives]"

HELP = """
Visit https://github.com/jkwill87/mnamer for more information.

PREFERENCES:
    The following flags can be used to customize mnamer's behaviour. Their long
    forms may also be set in a '.mnamer.json' config file, in which case cli
    arguments will take presenece.

    -b, --batch: batch mode; disables interactive prompts
    -s, --scene: scene mode; use dots in place of alphanumeric chars
    -r, --recurse: show this help message and exit
    -v, --verbose: increases output verbosity
    --blacklist <word,...>: ignores files matching these regular expressions
    --extmask <ext,...>: define extension mask used by the file parser
    --hits <number>: limits the maximum number of hits for each query
    --movie_api {tmdb}: set movie api provider
    --movie_destination <path>: set movie relocation destination
    --movie_template <template>: set movie renaming template
    --television_api {tvdb}: set television api provider
    --television_destination <path>: set television relocation destination
    --television_template <template>: set television renaming template

DIRECTIVES:
    Directives are one-off parameters that are used to perform secondary tasks like overriding media detection.

    --config: prints current config JSON to stdout then exits
    --help: prints this message then exits
    --id < id >: explicitly specify movie or series id
    --media { movie, television }: override media detection
    --test: mocks the renaming and moving of files
    --version: display running mnamer version number then exits
"""

VERSION = 1.4
