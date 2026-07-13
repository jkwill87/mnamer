//! Verifies deterministic filesystem discovery.

use super::*;
use std::fs;

#[test]
fn discovers_recursively_with_filters_and_deduplication() {
    let temp = tempfile::tempdir().unwrap();
    let nested = temp.path().join("nested");
    fs::create_dir(&nested).unwrap();
    fs::write(
        temp.path().join("Once.Upon.a.Time.in.Hollywood.2019.mkv"),
        b"movie",
    )
    .unwrap();
    fs::write(temp.path().join("The.Mask.1994.sample.mp4"), b"sample").unwrap();
    fs::write(nested.join("Succession.S01E01.Celebration.MP4"), b"episode").unwrap();
    fs::write(nested.join("notes.txt"), b"notes").unwrap();

    let options = DiscoveryOptions {
        recursive: true,
        ..DiscoveryOptions::default()
    };
    let result = discover(
        &[
            temp.path().to_path_buf(),
            nested.join("Succession.S01E01.Celebration.MP4"),
        ],
        &options,
    )
    .unwrap();

    assert_eq!(result.files.len(), 2);
    assert!(
        result
            .files
            .iter()
            .any(|path| path.ends_with("Once.Upon.a.Time.in.Hollywood.2019.mkv"))
    );
    assert!(
        result
            .files
            .iter()
            .any(|path| path.ends_with("Succession.S01E01.Celebration.MP4"))
    );
}

#[test]
fn non_recursive_discovery_stays_at_root() {
    let temp = tempfile::tempdir().unwrap();
    let nested = temp.path().join("nested");
    fs::create_dir(&nested).unwrap();
    fs::write(
        nested.join("Constellation.S01E01.The.Wounded.Angel.mkv"),
        b"episode",
    )
    .unwrap();
    let result = discover(&[temp.path().to_path_buf()], &DiscoveryOptions::default()).unwrap();
    assert!(result.files.is_empty());
}

#[test]
fn missing_paths_are_reported_without_aborting() {
    let temp = tempfile::tempdir().unwrap();
    let result = discover(
        &[temp.path().join("missing"), temp.path().to_path_buf()],
        &DiscoveryOptions::default(),
    )
    .unwrap();
    assert_eq!(result.failures.len(), 1);
    assert_eq!(result.failures[0].message, "path does not exist");
}

#[test]
fn invalid_glob_is_a_configuration_error() {
    let options = DiscoveryOptions {
        ignore: vec!["[".into()],
        ..DiscoveryOptions::default()
    };
    assert!(discover(&[], &options).is_err());
}

#[test]
fn default_discovery_includes_all_supported_subtitle_formats() {
    let directory = tempfile::tempdir().unwrap();
    for name in [
        "Ghost.in.the.Shell.2017.en.srt",
        "Motherless.Brooklyn.2019.en.idx",
        "Dark.Phoenix.2019.en.sub",
        "28.Days.Later.2002.en.ass",
        "Annabelle.2014.en.ssa",
        "Superbad.2007.en.vtt",
    ] {
        fs::write(directory.path().join(name), b"subtitle").unwrap();
    }

    let result = discover(
        &[directory.path().to_path_buf()],
        &DiscoveryOptions::default(),
    )
    .unwrap();

    assert_eq!(result.files.len(), 6);
}

#[cfg(unix)]
#[test]
fn explicit_symbolic_links_are_rejected_without_resolving_the_target() {
    use std::os::unix::fs::symlink;

    let directory = tempfile::tempdir().unwrap();
    let target = directory
        .path()
        .join("Boardwalk.Empire.S01E01.Boardwalk.Empire.mkv");
    let link = directory.path().join("Boardwalk.Empire.S01E01.mkv");
    std::fs::write(&target, b"movie").unwrap();
    symlink(&target, &link).unwrap();

    let result = discover(&[link], &DiscoveryOptions::default()).unwrap();

    assert!(result.files.is_empty());
    assert_eq!(result.failures.len(), 1);
    assert!(target.exists());
}
