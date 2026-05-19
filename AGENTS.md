# AGENTS.md

This file provides guidance to LLMs when working with code in this repository.

## Project Overview

mnamer (media renamer) is a command-line utility for organizing media files. It parses filenames for metadata using guessit, queries metadata providers (TMDb, OMDb, TVDb, TvMaze), and intelligently renames/moves files based on configurable templates.

## Development Setup

This project requires Python 3.12+ and uses `uv` as the package manager:

```bash
# Install dependencies
uv sync --dev

# Run mnamer locally
uv run mnamer [args]
```

## Common Commands

### Testing

The test suite is organized by pytest markers. Keep local tests free of network
access; network and e2e tests can be flaky because they exercise providers and
the CLI workflow.

```bash
# Run local unit tests (no network)
uv run pytest -m local

# Run network tests (requires internet, may be flaky)
uv run pytest -m network --reruns 3

# Run end-to-end tests
uv run pytest -m e2e --reruns 3

# Run all tests with coverage
uv run pytest --cov=./ --cov-report=term-missing

# Run a specific test file
uv run pytest tests/local/test_metadata.py

# Run a specific test function
uv run pytest tests/local/test_metadata.py::test_function_name
```

Registered markers are declared in `pytest.ini`: `local`, `network`, `e2e`,
plus provider markers `omdb`, `tmdb`, `tvdb`, and `tvmaze`.

### Linting and Formatting

```bash
# Check code with ruff
uv run ruff check mnamer tests

# Format code with ruff
uv run ruff format mnamer tests

# Type check with mypy
uv run mypy mnamer tests
```

## Architecture

### Core Data Flow

1. **Entry Point** (`__main__.py:main`): Loads settings and initializes the CLI frontend
2. **Frontend** (`frontends.py:Cli`): Orchestrates the file processing workflow
3. **Target** (`target.py:Target`): Represents a media file, manages its metadata and relocation
4. **Metadata** (`metadata.py`): Dataclasses for storing parsed and enriched metadata
   - `MetadataMovie`: Movie-specific fields (name, year, id_imdb, id_tmdb)
   - `MetadataEpisode`: TV episode fields (series, season, episode, id_tvdb, id_tvmaze)
5. **Providers** (`providers.py`): High-level interface for querying metadata APIs
   - `Tmdb`, `Omdb`: Movie providers
   - `Tvdb`, `Tvmaze`: TV episode providers
6. **Endpoints** (`endpoints.py`): Low-level API request functions and response TypedDicts

### Key Architectural Patterns

- **Metadata Parsing**: Uses `guessit` library to extract metadata from filenames. The `Target._parse()` method converts guessit output into `Metadata` objects.

- **Target Discovery**: `Target.populate_paths()` crawls positional targets, applies `--recurse`, `--ignore`, `--mask`, de-duplicates paths, and filters by `--media` when supplied.

- **Provider System**: Providers are registered per-provider in a class variable cache (`Target._providers`). `Provider.provider_factory()` instantiates providers based on the `ProviderType` enum and settings.

- **Settings Management**: `SettingStore` loads configuration from both CLI arguments (`argument.py:ArgLoader`) and JSON config files (`.mnamer-v2.json`). CLI args take precedence over config files. Config-only fields include API keys and replacement maps.

- **Template Formatting**: `MetadataMovie.__format__()` and `MetadataEpisode.__format__()` use `_MetaFormatter` to substitute template variables like `{name}`, `{season:02}`, and `{extension}`. Templates are configured per media type via settings.

- **File Relocation**: `Target.destination` combines the optional `movie_directory` or `episode_directory` setting with the matching format template, then applies replacement, scene/lowercase settings, and filename sanitization. `Target.relocate()` creates destination directories and moves the file.

### Important Implementation Details

- **Subtitle Handling**: Subtitle files (`.srt`, `.idx`, `.sub`) are detected via `is_subtitle()`. They use the same format pattern as their media type and, when subtitle language is known, prefix the extension with the 2-letter language code (e.g., `.en.srt`).

- **Language Support**: The `Language` class (in `language.py`) wraps babelfish for language code conversion. Providers return metadata in the language specified by `--language` setting.

- **Request Caching**: API requests go through `utils.get_session()`, a `requests-cache` `CachedSession` stored under the user cache directory for six days. Cache can be cleared with the `--clear-cache` directive or bypassed per run with `--no-cache`.

- **Error Handling**: Custom exceptions in `exceptions.py` distinguish between network errors (`MnamerNetworkException`), missing results (`MnamerNotFoundException`), and user actions (`MnamerSkipException`, `MnamerAbortException`).

- **Test Organization**:
  - `tests/local/`: Pure unit tests, no network or filesystem side effects
  - `tests/network/`: Integration tests hitting real APIs (may be flaky)
  - `tests/e2e/`: End-to-end tests with actual file operations

## Configuration

- **Config File**: `.mnamer-v2.json` in the current or parent directories, or the explicit path from `--config-path`
- **Settings Precedence**: CLI arguments > config file > defaults
- **Directives vs Parameters**: Directives (like `--test`, `--id-tmdb`) are one-time overrides not stored in config files
- **Config-only Fields**: `api_key_omdb`, `api_key_tmdb`, `api_key_tvdb`, `api_key_tvmaze`, `replace_before`, and `replace_after` are only loaded from config/defaults, not CLI flags

## API Keys

Providers load API keys through `Provider.from_settings()` using config-only
fields named `api_key_<provider>`. If unset, provider classes fall back to
environment variables (`API_KEY_OMDB`, `API_KEY_TMDB`, `API_KEY_TVDB`,
`API_KEY_TVMAZE`) and then bundled defaults where present.

Check provider classes in `providers.py` for API key handling via `from_settings()` class method.
