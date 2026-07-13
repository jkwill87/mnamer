# mnamer

<img src="assets/logo.png" alt="mnamer" width="450">

`mnamer` (**m**edia re**namer**) is a configurable Rust media organization utility. It parses media
filenames, looks up missing metadata, and moves, copies, or links files into consistent library
layouts.

Movie metadata comes from [TMDb](https://www.themoviedb.org/) or
[OMDb](https://www.omdbapi.com/). Episode metadata comes from
[TVmaze](https://www.tvmaze.com/) or [TVDb](https://thetvdb.com/).

## Documentation

💾 **Installation**

Install [mise](https://mise.jdx.dev/), then build the CLI with the pinned Rust toolchain:

```bash
git clone https://github.com/jkwill87/mnamer.git
cd mnamer
mise install
mise x -- cargo install --locked --path .
```

For development, run `mise x -- cargo run -- help`.

🤖 **Automation**

Use `--test` to resolve metadata and validate destinations without changing files. Use `--batch`
to select the highest-ranked match without prompting; `--json` implies batch mode.

```bash
mnamer move Downloads/ --recursive --test
mnamer copy Downloads/ --recursive --batch
mnamer hardlink Downloads/ --recursive --batch
mnamer symlink Downloads/ --recursive --batch
```

| Action     | Result                                                    |
| ---------- | --------------------------------------------------------- |
| `move`     | Moves each source; supports `--overwrite`                 |
| `copy`     | Copies each source; supports `--overwrite`                |
| `hardlink` | Creates a same-volume hard link and retains the source     |
| `symlink`  | Creates a symbolic link and retains the source             |

On Windows, `hardlink` and `symlink` are unavailable and omitted from CLI help; use `move` or
`copy` instead.

Every action checks all destinations before writing. Link actions never overwrite. Batch provider
misses remain unmatched unless `--allow-guess` is set.

Exit codes are `0` for success or no media, `1` for partial or failed processing, `2` for CLI or
configuration errors, and `130` when interrupted.

✍️ **Formatting**

Set filename and directory templates in `mnamer.toml` or with `--movie-format`,
`--episode-format`, `--movie-directory`, and `--episode-directory`.

```toml
[movie]
format = "{{ name }} ({{ year }}).{{ extension }}"
directory = "/media/movies/{{ name | first }}"

[episode]
format = "{{ series }} - S{{ season | pad: 2 }}E{{ episode | pad: 2 }} - {{ title }}.{{ extension }}"
directory = "/media/tv/{{ series }}"
```

Templates use [Upon](https://docs.rs/upon). Common values include `name`, `series`, `title`,
`year`, `season`, `episode`, `episodes`, `date`, `quality`, `language`, `extension`, and
provider IDs. `pad` zero-pads numbers and `first` returns the first character.

Use `--lowercase` for lowercase paths or `--scene` for scene-style names.

🌐 **Internationalization**

Use `--language <LANG>` or `matching.language` to select the provider and template language.
Language names and ISO 639 codes are accepted. TMDb and TVDb support localized responses.

Subtitle files in SRT, IDX/SUB, ASS, SSA, and VTT formats are grouped with their video. Language
markers are normalized to two-letter codes, and numeric tracks plus `forced`, `sdh`, and
`commentary` are retained, for example `.en.2.forced.srt`. Text subtitles without a language
marker can be detected from their contents; unresolved subtitles are prompted for interactively
or skipped in batch mode.

🧰 **Settings**

```text
A media file renaming and organization utility.

Usage: mnamer [OPTIONS] <COMMAND>

Commands:
  move      Rename media files, moving them to their target locations
  copy      Rename media files, copying them to their target locations
  hardlink  Create hard links at target locations, keeping source files in place
  symlink   Create symbolic links at target locations, keeping source files in place
  config    Inspect, validate, or initialize `mnamer.toml`
  cache     Inspect or clear the provider-response cache
  provider  List or verify metadata providers
  help      Print this message or the help of the given subcommand(s)
  version   Display the running mnamer version

Options:
      --config <PATH>  Use one explicit `mnamer.toml` file
      --json           Emit one structured JSON document
  -v, --verbose...     Increase diagnostic verbosity; may be repeated
```

Run `mnamer help <command>` for the complete options.

Configuration is loaded from the first match: an explicit `--config` path, the nearest
`mnamer.toml`, the OS-native configuration directory, or built-in defaults. Files are not
layered, and unknown settings are errors.

Use `mnamer config init` to create a documented starter file. `config show`, `config validate`,
and `config path` inspect the active configuration. Provider keys can be set under `[api_keys]`
or with `API_KEY_TMDB`, `API_KEY_OMDB`, and `API_KEY_TVDB`; TVmaze requires no key. Successful
responses are cached for six days by default.

## Contributions

Contributions and bug reports are welcome. Please
[open an issue](https://github.com/jkwill87/mnamer/issues) before making major CLI or
configuration changes.
