//! Verifies filesystem preflight and action application.

use super::*;
use crate::execute::Operation;
use crate::media::{MediaKind, Metadata};
use std::fs;
use std::time::{Duration, SystemTime};

#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;

fn options(action: Action) -> ApplyOptions {
    ApplyOptions {
        action,
        overwrite: false,
    }
}

fn ready(index: usize, source: PathBuf, destination: PathBuf) -> Operation {
    let mut item = Operation::unresolved(
        index,
        source,
        Metadata {
            media_type: MediaKind::Movie,
            ..Metadata::default()
        },
    );
    item.destination = Some(destination);
    item.outcome = OperationOutcome::Ready;
    item
}

#[test]
fn preflight_marks_every_duplicate_destination() {
    let directory = tempfile::tempdir().unwrap();
    let destination = directory.path().join("Smile.2022.mkv");
    let mut items = vec![
        ready(
            0,
            directory.path().join("Erin.Brockovich.2000.mkv"),
            destination.clone(),
        ),
        ready(1, directory.path().join("Candyman.2021.mkv"), destination),
    ];

    preflight(&mut items, options(Action::Move));

    assert!(
        items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Collision)
    );
}

#[test]
fn move_applies_video_and_subtitle_bundle_without_losing_contents() {
    let directory = tempfile::tempdir().unwrap();
    let source_directory = directory.path().join("source");
    let destination_directory = directory.path().join("library");
    fs::create_dir_all(&source_directory).unwrap();
    let fixtures = [
        (
            "Unhinged.2020.mkv",
            "Unhinged (2020).mkv",
            b"video".as_slice(),
        ),
        (
            "Unhinged.2020.en.srt",
            "Unhinged (2020).en.srt",
            b"srt".as_slice(),
        ),
        (
            "Unhinged.2020.en.idx",
            "Unhinged (2020).en.idx",
            b"idx".as_slice(),
        ),
        (
            "Unhinged.2020.en.sub",
            "Unhinged (2020).en.sub",
            b"sub".as_slice(),
        ),
    ];
    let mut items = fixtures
        .iter()
        .enumerate()
        .map(|(index, (source, destination, contents))| {
            let source = source_directory.join(source);
            fs::write(&source, contents).unwrap();
            ready(index, source, destination_directory.join(destination))
        })
        .collect::<Vec<_>>();

    let move_options = options(Action::Move);
    preflight(&mut items, move_options);
    apply(&mut items, move_options);

    assert!(
        items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Completed)
    );
    for (source, destination, contents) in fixtures {
        assert!(!source_directory.join(source).exists());
        assert_eq!(
            fs::read(destination_directory.join(destination)).unwrap(),
            contents
        );
    }
}

#[test]
fn preflight_protects_existing_destinations_and_directories() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Garden.State.2004.mkv");
    let destination = directory.path().join("Garden State (2004).mkv");
    let destination_directory = directory.path().join("library");
    fs::write(&source, b"source").unwrap();
    fs::write(&destination, b"existing").unwrap();
    fs::create_dir(&destination_directory).unwrap();
    let mut items = vec![
        ready(0, source.clone(), destination),
        ready(1, source, destination_directory),
    ];

    preflight(
        &mut items,
        ApplyOptions {
            action: Action::Copy,
            overwrite: true,
        },
    );

    assert_eq!(items[0].outcome, OperationOutcome::Ready);
    assert_eq!(items[1].outcome, OperationOutcome::Exists);
}

#[test]
fn preflight_rejects_destinations_that_are_other_sources() {
    let directory = tempfile::tempdir().unwrap();
    let first = directory.path().join("The.Money.Pit.1986.mkv");
    let second = directory.path().join("Rush.Hour.3.2007.mkv");
    fs::write(&first, b"first").unwrap();
    fs::write(&second, b"second").unwrap();
    let mut items = vec![
        ready(0, first, second.clone()),
        ready(1, second, directory.path().join("Hercules.1997.mkv")),
    ];

    preflight(
        &mut items,
        ApplyOptions {
            action: Action::Move,
            overwrite: true,
        },
    );

    assert!(
        items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Collision)
    );
}

#[test]
fn application_continues_after_per_item_failures() {
    let directory = tempfile::tempdir().unwrap();
    let valid_source = directory.path().join("The.Incredible.Hulk.2008.mkv");
    let valid_destination = directory
        .path()
        .join("nested/The Incredible Hulk (2008).mkv");
    fs::write(&valid_source, b"movie").unwrap();
    let mut items = vec![
        ready(
            0,
            directory.path().join("GOAT.2026.mkv"),
            directory.path().join("GOAT (2026).mkv"),
        ),
        ready(1, valid_source.clone(), valid_destination.clone()),
    ];

    apply(&mut items, options(Action::Move));

    assert_eq!(items[0].outcome, OperationOutcome::Failed);
    assert_eq!(items[1].outcome, OperationOutcome::Completed);
    assert!(!valid_source.exists());
    assert_eq!(fs::read(valid_destination).unwrap(), b"movie");
}

#[test]
fn exact_source_destination_paths_are_unchanged_for_every_action() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Irreversible.2002.mkv");
    fs::write(&source, b"movie").unwrap();

    #[cfg(windows)]
    let actions = [Action::Move, Action::Copy].as_slice();
    #[cfg(not(windows))]
    let actions = [
        Action::Move,
        Action::Copy,
        Action::Hardlink,
        Action::Symlink,
    ]
    .as_slice();

    for &action in actions {
        let mut items = vec![ready(0, source.clone(), source.clone())];
        preflight(&mut items, options(action));
        assert_eq!(items[0].outcome, OperationOutcome::Unchanged);
    }
}

#[test]
fn copy_retains_an_independent_source_and_preserves_portable_metadata() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Talk.to.Me.2022.mkv");
    let destination = directory.path().join("library/Talk to Me (2022).mkv");
    fs::write(&source, b"movie").unwrap();
    let accessed = SystemTime::UNIX_EPOCH + Duration::from_secs(1_699_999_000);
    let modified = SystemTime::UNIX_EPOCH + Duration::from_secs(1_700_000_000);
    let source_file = fs::OpenOptions::new().write(true).open(&source).unwrap();
    source_file
        .set_times(
            fs::FileTimes::new()
                .set_accessed(accessed)
                .set_modified(modified),
        )
        .unwrap();
    drop(source_file);
    #[cfg(unix)]
    fs::set_permissions(&source, fs::Permissions::from_mode(0o640)).unwrap();
    let mut items = vec![ready(0, source.clone(), destination.clone())];

    let copy_options = options(Action::Copy);
    preflight(&mut items, copy_options);
    apply(&mut items, copy_options);

    assert_eq!(items[0].outcome, OperationOutcome::Completed);
    let destination_metadata = fs::metadata(&destination).unwrap();
    assert_eq!(destination_metadata.accessed().unwrap(), accessed);
    assert_eq!(destination_metadata.modified().unwrap(), modified);
    #[cfg(unix)]
    assert_eq!(destination_metadata.permissions().mode() & 0o777, 0o640);
    assert_eq!(fs::read(&source).unwrap(), b"movie");
    assert_eq!(fs::read(&destination).unwrap(), b"movie");
    fs::write(&source, b"changed").unwrap();
    assert_eq!(
        fs::read(items[0].destination.as_ref().unwrap()).unwrap(),
        b"movie"
    );
}

#[test]
fn copy_overwrite_replaces_destination_without_removing_source() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Scream.7.2026.mkv");
    let destination = directory.path().join("Scream 7 (2026).mkv");
    fs::write(&source, b"new").unwrap();
    fs::write(&destination, b"old").unwrap();
    let mut items = vec![ready(0, source.clone(), destination.clone())];
    let copy_options = ApplyOptions {
        action: Action::Copy,
        overwrite: true,
    };

    preflight(&mut items, copy_options);
    apply(&mut items, copy_options);

    assert!(source.exists());
    assert_eq!(fs::read(destination).unwrap(), b"new");
}

#[cfg(not(windows))]
#[test]
fn hardlink_creates_shared_identity_and_is_idempotent() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Heat.1995.mkv");
    let destination = directory.path().join("library/Heat (1995).mkv");
    fs::write(&source, b"movie").unwrap();
    let hardlink_options = options(Action::Hardlink);
    let mut items = vec![ready(0, source.clone(), destination.clone())];

    preflight(&mut items, hardlink_options);
    apply(&mut items, hardlink_options);

    assert_eq!(items[0].outcome, OperationOutcome::Completed);
    assert!(same_regular_file(&source, &destination));
    fs::write(&source, b"changed").unwrap();
    assert_eq!(fs::read(&destination).unwrap(), b"changed");

    let mut repeated = vec![ready(0, source, destination)];
    preflight(&mut repeated, hardlink_options);
    assert_eq!(repeated[0].outcome, OperationOutcome::Unchanged);
}

#[cfg(unix)]
#[test]
fn symlink_creates_an_absolute_target_and_is_idempotent() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Thief.1981.mkv");
    let destination = directory.path().join("library/Thief (1981).mkv");
    fs::write(&source, b"movie").unwrap();
    let symlink_options = options(Action::Symlink);
    let mut items = vec![ready(0, source.clone(), destination.clone())];

    preflight(&mut items, symlink_options);
    apply(&mut items, symlink_options);

    assert_eq!(items[0].outcome, OperationOutcome::Completed);
    let target = fs::read_link(&destination).unwrap();
    assert!(target.is_absolute());
    assert_eq!(target, source.canonicalize().unwrap());
    assert_eq!(fs::read(&destination).unwrap(), b"movie");

    let mut repeated = vec![ready(0, source, destination)];
    preflight(&mut repeated, symlink_options);
    assert_eq!(repeated[0].outcome, OperationOutcome::Unchanged);
}

#[cfg(unix)]
#[test]
fn an_equivalent_relative_symlink_is_not_treated_as_the_managed_absolute_link() {
    use std::os::unix::fs::symlink;

    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Thief.1981.mkv");
    let destination = directory.path().join("Thief (1981).mkv");
    fs::write(&source, b"movie").unwrap();
    symlink(source.file_name().unwrap(), &destination).unwrap();
    let mut items = vec![ready(0, source, destination)];

    preflight(&mut items, options(Action::Symlink));

    assert_eq!(items[0].outcome, OperationOutcome::Exists);
}

#[test]
fn cross_filesystem_move_fallback_copies_then_removes_source() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Gladiator.II.2024.mkv");
    let destination = directory.path().join("library/Gladiator II (2024).mkv");
    fs::write(&source, b"movie").unwrap();

    r#move::copy_then_remove(&source, &destination, false).unwrap();

    assert!(!source.exists());
    assert_eq!(fs::read(destination).unwrap(), b"movie");
}

#[test]
fn preflight_never_creates_destination_parents() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("Candyman.1992.mkv");
    fs::write(&source, b"movie").unwrap();

    #[cfg(windows)]
    let actions = [Action::Move, Action::Copy].as_slice();
    #[cfg(not(windows))]
    let actions = [
        Action::Move,
        Action::Copy,
        Action::Hardlink,
        Action::Symlink,
    ]
    .as_slice();

    for &action in actions {
        let parent = directory.path().join(action.as_str());
        let mut items = vec![ready(0, source.clone(), parent.join("Candyman (1992).mkv"))];
        preflight(&mut items, options(action));
        assert!(!parent.exists());
    }
}

#[cfg(not(windows))]
#[test]
fn volume_comparison_only_rejects_known_mismatches() {
    assert!(volume_ids_differ(Some(1), Some(2)));
    assert!(!volume_ids_differ(Some(1), Some(1)));
    assert!(!volume_ids_differ(Some(1), None));
    assert!(!volume_ids_differ(None, Some(2)));
}

#[test]
fn interrupt_stops_before_the_next_ready_write() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("The.Bone.Collector.1999.mkv");
    fs::write(&source, b"movie").unwrap();
    let mut items = vec![ready(
        0,
        source.clone(),
        directory.path().join("The Bone Collector (1999).mkv"),
    )];

    let interrupted = apply_interruptible(&mut items, options(Action::Move), || true);

    assert!(interrupted);
    assert_eq!(items[0].outcome, OperationOutcome::Skipped);
    assert!(source.exists());
}

#[test]
fn move_never_clobbers_without_overwrite_and_replaces_with_it() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("The.Toxic.Avenger.Unrated.2025.mkv");
    let destination = directory
        .path()
        .join("The Toxic Avenger Unrated (2025).mkv");
    fs::write(&source, b"new").unwrap();
    fs::write(&destination, b"old").unwrap();

    let error = r#move::apply(&source, &destination, false).unwrap_err();
    assert_eq!(error.kind(), io::ErrorKind::AlreadyExists);
    assert_eq!(fs::read(&source).unwrap(), b"new");
    assert_eq!(fs::read(&destination).unwrap(), b"old");

    r#move::apply(&source, &destination, true).unwrap();
    assert!(!source.exists());
    assert_eq!(fs::read(&destination).unwrap(), b"new");
}

#[test]
fn move_supports_case_only_destination_changes() {
    let directory = tempfile::tempdir().unwrap();
    let source = directory.path().join("goodfellas.mkv");
    let destination = directory.path().join("GoodFellas.mkv");
    fs::write(&source, b"movie").unwrap();

    r#move::apply(&source, &destination, false).unwrap();

    assert_eq!(fs::read(&destination).unwrap(), b"movie");
}

#[cfg(any(target_os = "macos", windows))]
#[test]
fn preflight_case_folds_destination_collision_keys() {
    let directory = tempfile::tempdir().unwrap();
    let mut items = vec![
        ready(
            0,
            directory.path().join("Star.Trek.Generations.1994.mkv"),
            directory.path().join("Scream.mkv"),
        ),
        ready(
            1,
            directory.path().join("Star.Trek.Insurrection.1998.mkv"),
            directory.path().join("scream.mkv"),
        ),
    ];

    preflight(
        &mut items,
        ApplyOptions {
            action: Action::Copy,
            overwrite: true,
        },
    );

    assert!(
        items
            .iter()
            .all(|item| item.outcome == OperationOutcome::Collision)
    );
}
