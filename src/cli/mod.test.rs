//! Verifies command-line parsing and validation.

use super::*;
use crate::config::{Config, EpisodeProvider, MovieProvider};
use crate::net::provider::ProviderKind;
use std::path::PathBuf;

fn parse(args: &[&str]) -> Cli {
    Cli::try_parse_validated_from(args).unwrap()
}

#[test]
fn parses_complete_move_command() {
    let cli = parse(&[
        "mnamer",
        "move",
        "shows",
        "Anora.2024.mkv",
        "--recursive",
        "--extension",
        ".MKV",
        "--extension=mp4",
        "--ignore",
        "**/sample/**",
        "--media",
        "episode",
        "--movie-provider",
        "omdb",
        "--episode-provider",
        "tvdb",
        "--language",
        "fr",
        "--max-results",
        "9",
        "--id",
        "tvdb:1234",
        "--allow-guess",
        "--movie-format",
        "movie-template",
        "--episode-format",
        "episode-template",
        "--movie-directory",
        "movies",
        "--episode-directory",
        "episodes",
        "--lowercase",
        "--scene",
        "--batch",
        "--jobs",
        "8",
        "--test",
        "--overwrite",
        "--no-cache",
        "--no-file-inspection",
    ]);

    let Command::Move { args, overwrite } = cli.command else {
        panic!("expected move command");
    };
    assert_eq!(
        args.paths,
        [PathBuf::from("shows"), PathBuf::from("Anora.2024.mkv")]
    );
    assert!(args.recursive);
    assert_eq!(args.extensions, ["mkv", "mp4"]);
    assert_eq!(args.ignore, ["**/sample/**"]);
    assert_eq!(args.media, MediaMode::Episode);
    assert_eq!(args.movie_provider, Some(MovieProvider::Omdb));
    assert_eq!(args.episode_provider, Some(EpisodeProvider::Tvdb));
    assert_eq!(args.language.as_deref(), Some("fr"));
    assert_eq!(args.max_results, Some(9));
    assert_eq!(
        args.external_id,
        Some(ExternalId {
            source: ExternalIdSource::Tvdb,
            value: "1234".to_owned(),
        })
    );
    assert!(args.allow_guess);
    assert_eq!(args.movie_format.as_deref(), Some("movie-template"));
    assert_eq!(args.episode_format.as_deref(), Some("episode-template"));
    assert_eq!(args.movie_directory.as_deref(), Some("movies"));
    assert_eq!(args.episode_directory.as_deref(), Some("episodes"));
    assert!(args.lowercase);
    assert!(args.scene);
    assert!(args.batch);
    assert_eq!(args.jobs, Some(8));
    assert!(args.test);
    assert!(overwrite);
    assert!(args.no_cache);
    assert!(args.no_file_inspection);
    assert!(!args.file_inspection);
}

#[test]
fn file_inspection_flags_override_configuration_and_conflict() {
    let mut config = Config::default();
    config.inspection.file_content = false;
    let enabled = parse(&["mnamer", "move", "movie.mkv", "--file-inspection"]);
    assert!(
        enabled
            .execution_options(&config)
            .unwrap()
            .unwrap()
            .file_inspection
    );

    config.inspection.file_content = true;
    let disabled = parse(&["mnamer", "move", "movie.mkv", "--no-file-inspection"]);
    assert!(
        !disabled
            .execution_options(&config)
            .unwrap()
            .unwrap()
            .file_inspection
    );

    let conflict = Cli::try_parse_validated_from([
        "mnamer",
        "move",
        "movie.mkv",
        "--file-inspection",
        "--no-file-inspection",
    ]);
    assert!(conflict.is_err());
}

#[test]
fn accepts_globals_after_nested_command_and_paths() {
    let cli = parse(&[
        "mnamer",
        "copy",
        "Argylle.2024.mkv",
        "--json",
        "--config",
        "settings.toml",
        "-vv",
        "--jobs",
        "3",
    ]);

    assert!(cli.json);
    assert_eq!(cli.config, Some(PathBuf::from("settings.toml")));
    assert_eq!(cli.verbose, 2);
    let Command::Copy { args, .. } = cli.command else {
        panic!("expected copy command");
    };
    assert!(args.effective_batch(cli.json));
    assert_eq!(args.jobs, Some(3));
}

#[test]
fn json_is_accepted_for_every_command_family() {
    for args in [
        vec!["mnamer", "version", "--json"],
        vec!["mnamer", "move", "Baraka.1992.mkv", "--json"],
        vec!["mnamer", "copy", "Bloodsport.1988.mkv", "--json"],
        vec!["mnamer", "config", "show", "--json"],
        vec!["mnamer", "cache", "path", "--json"],
        vec!["mnamer", "provider", "list", "--json"],
    ] {
        assert!(parse(&args).json, "failed for {args:?}");
    }

    #[cfg(not(windows))]
    for args in [
        ["mnamer", "hardlink", "Brazil.1985.mkv", "--json"],
        ["mnamer", "symlink", "Burning.2018.mkv", "--json"],
    ] {
        assert!(parse(&args).json, "failed for {args:?}");
    }
}

#[cfg(windows)]
#[test]
fn link_commands_are_unavailable_on_windows() {
    for command in ["hardlink", "symlink"] {
        assert!(Cli::try_parse_validated_from(["mnamer", command, "movie.mkv"]).is_err());
    }
}

#[test]
fn version_is_a_subcommand_instead_of_a_flag() {
    let cli = parse(&["mnamer", "version"]);
    assert_eq!(cli.command, Command::Version);
    assert_eq!(cli.command.name(), "version");
    assert!(cli.execution_options(&Config::default()).is_none());

    for flag in ["-V", "--version"] {
        assert!(
            Cli::try_parse_validated_from(["mnamer", flag]).is_err(),
            "unexpectedly accepted {flag}"
        );
    }
}

#[test]
fn parses_maintenance_command_tree() {
    let cli = parse(&["mnamer", "config", "path"]);
    assert!(matches!(
        cli.command.config_command(),
        Some(ConfigCommand::Path)
    ));

    let cli = parse(&["mnamer", "config", "validate", "custom.toml"]);
    assert_eq!(
        cli.command
            .config_command()
            .and_then(ConfigCommand::path_argument),
        Some(&PathBuf::from("custom.toml"))
    );

    let cli = parse(&["mnamer", "config", "init", "custom.toml", "--force"]);
    let command = cli.command.config_command().unwrap();
    assert_eq!(command.path_argument(), Some(&PathBuf::from("custom.toml")));
    assert!(command.force());

    let cli = parse(&["mnamer", "cache", "clear"]);
    assert_eq!(cli.command.cache_command(), Some(&CacheCommand::Clear));

    let cli = parse(&["mnamer", "provider", "check", "tvdb", "tmdb"]);
    assert_eq!(
        cli.command.provider_command().unwrap().providers(),
        [ProviderKind::Tvdb, ProviderKind::Tmdb]
    );

    let cli = parse(&["mnamer", "provider", "check"]);
    assert!(
        cli.command
            .provider_command()
            .unwrap()
            .providers()
            .is_empty()
    );
}

#[test]
fn requires_an_explicit_command_and_processing_path() {
    assert!(Cli::try_parse_validated_from(["mnamer"]).is_err());
    assert!(Cli::try_parse_validated_from(["mnamer", "move"]).is_err());
    assert!(Cli::try_parse_validated_from(["mnamer", "config"]).is_err());
}

#[test]
fn removes_legacy_commands_and_limits_overwrite_to_move_and_copy() {
    for command in ["preview", "rename"] {
        assert!(Cli::try_parse_validated_from(["mnamer", command, "movie.mkv"]).is_err());
    }
    for command in ["hardlink", "symlink"] {
        assert!(
            Cli::try_parse_validated_from(["mnamer", command, "movie.mkv", "--overwrite",])
                .is_err()
        );
    }
    for command in ["move", "copy"] {
        assert!(
            Cli::try_parse_validated_from(["mnamer", command, "movie.mkv", "--overwrite",]).is_ok()
        );
    }
}

#[test]
fn removed_global_options_are_rejected() {
    for args in [
        ["mnamer", "--no-config", "config", "show"].as_slice(),
        ["mnamer", "--color", "never", "config", "show"].as_slice(),
    ] {
        assert!(Cli::try_parse_validated_from(args).is_err());
    }
}

#[test]
fn jobs_requires_batch_unless_json_implies_it() {
    let error = Cli::try_parse_validated_from([
        "mnamer",
        "move",
        "Bicentennial.Man.1999.mkv",
        "--jobs",
        "2",
    ])
    .unwrap_err();
    assert!(
        error
            .to_string()
            .contains("--jobs requires --batch or --json")
    );

    assert!(
        Cli::try_parse_validated_from([
            "mnamer",
            "move",
            "Asteroid.City.2023.mkv",
            "--json",
            "--jobs",
            "2",
        ])
        .is_ok()
    );
}

#[test]
fn rejects_invalid_bounded_and_structured_values() {
    for args in [
        vec![
            "mnamer",
            "move",
            "A.Scanner.Darkly.2006.mkv",
            "--jobs",
            "0",
            "--batch",
        ],
        vec![
            "mnamer",
            "move",
            "Basic.Instinct.1992.mkv",
            "--jobs",
            "33",
            "--batch",
        ],
        vec!["mnamer", "move", "Bedazzled.2000.mkv", "--max-results", "0"],
        vec![
            "mnamer",
            "move",
            "Alita.Battle.Angel.2019.mkv",
            "--extension",
            ".",
        ],
        vec!["mnamer", "move", "Body.Heat.1981.mkv", "--extension", "a/b"],
        vec!["mnamer", "move", "Battle.Royale.2000.mkv", "--ignore", "["],
        vec!["mnamer", "move", "Black.Snake.Moan.2006.mkv", "--id", "123"],
        vec![
            "mnamer",
            "move",
            "Alien.Covenant.2017.mkv",
            "--id",
            "bad:123",
        ],
        vec![
            "mnamer",
            "move",
            "American.Beauty.1999.mkv",
            "--id",
            "tmdb:",
        ],
        vec![
            "mnamer",
            "move",
            "Blazing.Saddles.1974.mkv",
            "--id",
            "tmdb:1:2",
        ],
    ] {
        assert!(
            Cli::try_parse_validated_from(args.clone()).is_err(),
            "unexpectedly accepted {args:?}"
        );
    }
}

#[test]
fn typed_external_ids_round_trip() {
    for source in [
        ExternalIdSource::Imdb,
        ExternalIdSource::Tmdb,
        ExternalIdSource::Tvdb,
        ExternalIdSource::Tvmaze,
    ] {
        let id = if source == ExternalIdSource::Imdb {
            "tt123"
        } else {
            "123"
        };
        let value: ExternalId = format!("{source}:{id}").parse().unwrap();
        assert_eq!(value.source, source);
        assert_eq!(value.to_string(), format!("{source}:{id}"));
    }
}

#[test]
fn resolves_cli_values_over_file_configuration() {
    let mut config = Config::default();
    config.discovery.recursive = true;
    config.discovery.extensions = vec!["avi".to_owned()];
    config.discovery.ignore = vec!["configured/**".to_owned()];
    config.matching.language = "en".to_owned();
    config.matching.max_results = 5;
    config.matching.allow_guess = true;
    config.execution.jobs = 6;
    config.formatting.lowercase = true;
    config.movie.provider = MovieProvider::Tmdb;
    config.movie.format = "configured movie".to_owned();
    config.episode.provider = EpisodeProvider::Tvmaze;
    config.episode.directory = Some("configured episodes".to_owned());
    config.cache.enabled = true;

    let cli = parse(&[
        "mnamer",
        "move",
        "Beau.is.Afraid.2023.mkv",
        "--extension",
        "mkv",
        "--ignore",
        "cli/**",
        "--language",
        "fr",
        "--max-results",
        "2",
        "--movie-provider",
        "omdb",
        "--episode-provider",
        "tvdb",
        "--movie-format",
        "cli movie",
        "--episode-directory",
        "cli episodes",
        "--scene",
        "--no-cache",
        "--test",
        "--json",
    ]);
    let options = cli.execution_options(&config).unwrap().unwrap();

    assert_eq!(options.paths, [PathBuf::from("Beau.is.Afraid.2023.mkv")]);
    assert!(options.recursive);
    assert_eq!(options.extensions, ["mkv"]);
    assert_eq!(options.ignore, ["cli/**"]);
    assert_eq!(options.language, "fr");
    assert_eq!(options.max_results, 2);
    assert!(options.allow_guess);
    assert_eq!(options.movie_provider, MovieProvider::Omdb);
    assert_eq!(options.episode_provider, EpisodeProvider::Tvdb);
    assert_eq!(options.movie_format, "cli movie");
    assert_eq!(options.episode_directory.as_deref(), Some("cli episodes"));
    assert!(options.lowercase);
    assert!(options.scene);
    assert!(options.batch);
    assert_eq!(options.jobs, 6);
    assert_eq!(options.action, crate::execute::Action::Move);
    assert!(options.test);
    assert!(!options.overwrite);
    assert!(!options.use_cache);
    assert!(options.file_inspection);
}

#[test]
fn maintenance_commands_have_no_execution_options() {
    let cli = parse(&["mnamer", "config", "show"]);
    assert!(cli.execution_options(&Config::default()).is_none());
    assert_eq!(cli.command.name(), "config");
}
