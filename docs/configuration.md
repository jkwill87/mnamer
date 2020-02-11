# Settings

## Preferences

mnamer attempts to load _preferences_ from a **.mnamer-v2.json** file in the home directory, the current working directory, and then in each directory up the drive towards the drive root.

| Preference          | Arguments              | Description                                                     |
| :------------------ | :--------------------- | :-------------------------------------------------------------- |
| -b, --batch         |                        | batch mode; disable interactive prompts                         |
| -l, --lower         |                        | rename files using lowercase characters only                    |
| -r, --recurse       |                        | search for files in nested directories                          |
| -s, --scene         |                        | scene mode; replace non ascii-alphanumerics with `.`            |
| -v, --verbose       |                        | increase output verbosity                                       |
| --hits              | number                 | limit the maximum number of hits for each query                 |
| --ignore            | pattern                | ignore files including these words \(regex\)                    |
| --mask              | extension\(s\)         | only process files with given extensions                        |
| --nocache           |                        | disable and clear result cache                                  |
| --noguess           |                        | disable best guess fallback; e.g. when no matches, network down |
| --noreplace         |                        | prevent relocation if it would overwrite a file                 |
| --nostyle           |                        | disable colours and uses ASCII characters for prompts           |
| --movie-api         | **`tmdb`** or `omdb`   | set movie api provider                                          |
| --movie-directory   | path                   | set movie relocation directory                                  |
| --movie-format      | format                 | set movie renaming format                                       |
| --episode-api       | **`tvmaze`** or `tvdb` | set episode api provider                                        |
| --episode-directory | path                   | set episode relocation directory                                |
| --episode-format    | format                 | set episode renaming format                                     |

## Directives

Whereas preferences configure how mnamer works, _directives_ are one-off parameters that are used to perform secondary tasks like exporting the current option set to a file.

| Directive       | Arguments            | Description                               |
| :-------------- | :------------------- | :---------------------------------------- |
| -V, --version   |                      | display the running mnamer version number |
| --config-dump   |                      | prints config JSON to stdout then exits   |
| --config-ignore |                      | skips loading config file for session     |
| --id-imdb       | id                   | specify an IMDb movie id override         |
| --id-tmdb       | id                   | specify a TMDb movie id override          |
| --id-tvdb       | id                   | specify a TVDb series id override         |
| --id-tvmaze     | id                   | specify a TvMaze series id override       |
| --media         | `movie` or `episode` | override media detection                  |
| --test          |                      | mocks the renaming and moving of files    |

### Saving Preferences

The --config-dump directive writes the current program preferences to stdout as json.

It can be used along with other arguments and will include preferences from any other loaded configuration files. If you want to ignore any loaded configuration files, e.g. to get the default configuration, you can use `--config-ignore` along with `--config-dump`.

There are many ways to capture this and save it as a file, e.g. using pipes to stream the output to a file in MacOS, Linux, and Unix systems:

```bash
mnamer --config > .mnamer-v2.json.tmp
&& mv mnamer-v2.json.tmp .mnamer-v2.json
```

{% hint style="danger" %}
Take care not to write to a location that mnamer reads from because the stream will be created and opened for writing beforehand, resulting in an error. Either output to a temporary file before renaming to .mnamer-v2.json as in the example above, or use a tool like [moreutils' sponge](https://joeyh.name/code/moreutils).
{% endhint %}

### Passing IDs

When using `--id` to specify a movie or series id you can can use the following sources for each provider:

| Provider | Accepted IDs |
| :------- | :----------- |
| OMDb     | IMDb         |
| TMDb     | TMDb, IMDb   |
| TVDb     | TVDb, IMDb   |
| TVMaze   | TVMaze, TVDb |
