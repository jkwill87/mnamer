//! Preflights and applies filesystem actions sequentially.

mod copy;
#[cfg(not(windows))]
mod hardlink;
mod r#move;
#[cfg(not(windows))]
mod symlink;

use super::{Action, Operation, OperationOutcome};
use std::collections::HashMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

/// Options controlling preflight and filesystem application.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ApplyOptions {
    /// Filesystem action applied to every ready operation.
    pub action: Action,
    /// Whether move or copy may replace an existing destination entry.
    pub overwrite: bool,
}

impl Default for ApplyOptions {
    fn default() -> Self {
        Self {
            action: Action::Move,
            overwrite: false,
        }
    }
}

/// Validates every planned destination before any filesystem mutation.
///
/// Every member of an intra-run collision is marked as failed. Existing
/// destinations are protected unless move or copy explicitly enables
/// overwrite. Exact source/destination paths and already-correct links become
/// unchanged. Hard links on definitely different volumes fail read-only
/// preflight.
pub fn preflight(items: &mut [Operation], options: ApplyOptions) {
    #[cfg(not(windows))]
    if options.overwrite && matches!(options.action, Action::Hardlink | Action::Symlink) {
        for item in items
            .iter_mut()
            .filter(|item| item.outcome == OperationOutcome::Ready)
        {
            item.outcome = OperationOutcome::Failed;
            item.message = Some(format!(
                "--overwrite is not supported for {} operations",
                options.action
            ));
        }
        return;
    }

    let sources = items
        .iter()
        .enumerate()
        .map(|(position, item)| (collision_key(&item.source), position))
        .collect::<HashMap<_, _>>();
    let mut destinations: HashMap<PathBuf, Vec<usize>> = HashMap::new();

    for (position, item) in items.iter_mut().enumerate() {
        if item.outcome != OperationOutcome::Ready {
            continue;
        }
        let Some(destination) = item.destination.as_ref() else {
            item.outcome = OperationOutcome::Failed;
            item.message = Some("no destination was produced".into());
            continue;
        };
        if same_lexical_path(&item.source, destination) {
            item.outcome = OperationOutcome::Unchanged;
            item.message = None;
            continue;
        }
        destinations
            .entry(collision_key(destination))
            .or_default()
            .push(position);
    }

    for positions in destinations
        .values()
        .filter(|positions| positions.len() > 1)
    {
        for &position in positions {
            let item = &mut items[position];
            item.outcome = OperationOutcome::Collision;
            item.message = Some("multiple sources resolve to this destination".into());
        }
    }

    let mut source_conflicts = Vec::new();
    for (position, item) in items.iter().enumerate() {
        if item.outcome != OperationOutcome::Ready {
            continue;
        }
        if let Some(destination) = item.destination.as_deref()
            && let Some(&source_position) = sources.get(&collision_key(destination))
            && source_position != position
        {
            source_conflicts.push((position, source_position));
        }
    }
    for (position, source_position) in source_conflicts {
        items[position].outcome = OperationOutcome::Collision;
        items[position].message = Some("a destination is another planned source path".into());
        items[source_position].outcome = OperationOutcome::Collision;
        items[source_position].message =
            Some("a destination is another planned source path".into());
    }

    for item in items
        .iter_mut()
        .filter(|item| item.outcome == OperationOutcome::Ready)
    {
        let Some(destination) = item.destination.as_deref() else {
            continue;
        };
        if let Ok(metadata) = fs::symlink_metadata(destination) {
            let already_correct = match options.action {
                #[cfg(not(windows))]
                Action::Hardlink => same_regular_file(&item.source, destination),
                #[cfg(not(windows))]
                Action::Symlink => symlink_points_to(&item.source, destination),
                Action::Move | Action::Copy => false,
            };
            if already_correct {
                item.outcome = OperationOutcome::Unchanged;
                item.message = None;
                continue;
            }
            if metadata.file_type().is_dir() {
                item.outcome = OperationOutcome::Exists;
                item.message = Some("destination is a directory and cannot be replaced".into());
                continue;
            }
            if options.action == Action::Move && same_regular_file(&item.source, destination) {
                continue;
            }
            if !options.overwrite {
                item.outcome = OperationOutcome::Exists;
                item.message = Some(if matches!(options.action, Action::Move | Action::Copy) {
                    "destination already exists (use --overwrite to replace it)".into()
                } else {
                    "destination already exists".into()
                });
                continue;
            }
        }

        #[cfg(not(windows))]
        {
            if options.action == Action::Hardlink
                && hardlink_definitely_crosses_volumes(&item.source, destination)
            {
                item.outcome = OperationOutcome::Failed;
                item.message =
                    Some("hard links require source and destination on the same volume".into());
            }
        }
    }
}

/// Applies ready operations sequentially in deterministic order.
pub fn apply(items: &mut [Operation], options: ApplyOptions) {
    apply_interruptible(items, options, || false);
}

/// Applies ready operations until an interrupt is observed between writes.
///
/// An action already in progress finishes its critical section. Remaining
/// ready items are then marked skipped.
pub fn apply_interruptible(
    items: &mut [Operation],
    options: ApplyOptions,
    interrupted: impl Fn() -> bool,
) -> bool {
    for position in 0..items.len() {
        if items[position].outcome != OperationOutcome::Ready {
            continue;
        }
        if interrupted() {
            for item in items
                .iter_mut()
                .skip(position)
                .filter(|item| item.outcome == OperationOutcome::Ready)
            {
                item.outcome = OperationOutcome::Skipped;
                item.message = Some("interrupted before filesystem write".into());
            }
            return true;
        }
        let item = &mut items[position];
        let Some(destination) = item.destination.clone() else {
            item.outcome = OperationOutcome::Failed;
            item.message = Some("no destination was produced".into());
            continue;
        };
        match apply_one(&item.source, &destination, options) {
            Ok(()) => {
                item.outcome = OperationOutcome::Completed;
                item.message = None;
            }
            Err(error) => {
                item.outcome = OperationOutcome::Failed;
                item.message = Some(error.to_string());
            }
        }
    }
    false
}

/// Applies one preflighted filesystem operation.
fn apply_one(source: &Path, destination: &Path, options: ApplyOptions) -> io::Result<()> {
    #[cfg(not(windows))]
    if options.overwrite && matches!(options.action, Action::Hardlink | Action::Symlink) {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!(
                "overwrite is not supported for {} operations",
                options.action
            ),
        ));
    }
    match options.action {
        Action::Move => r#move::apply(source, destination, options.overwrite),
        Action::Copy => copy::apply(source, destination, options.overwrite),
        #[cfg(not(windows))]
        Action::Hardlink => hardlink::apply(source, destination),
        #[cfg(not(windows))]
        Action::Symlink => symlink::apply(source, destination),
    }
}

/// Creates the destination parent directory.
pub(super) fn create_parent(destination: &Path) -> io::Result<()> {
    fs::create_dir_all(destination.parent().unwrap_or_else(|| Path::new(".")))
}

/// Returns whether two paths are lexically equivalent.
pub(super) fn same_lexical_path(left: &Path, right: &Path) -> bool {
    lexical_absolute(left) == lexical_absolute(right)
}

/// Returns whether two paths identify the same regular file.
pub(super) fn same_regular_file(left: &Path, right: &Path) -> bool {
    let Ok(left_metadata) = fs::symlink_metadata(left) else {
        return false;
    };
    let Ok(right_metadata) = fs::symlink_metadata(right) else {
        return false;
    };
    if !left_metadata.file_type().is_file() || !right_metadata.file_type().is_file() {
        return false;
    }
    same_metadata_identity(&left_metadata, &right_metadata, left, right)
}

#[cfg(unix)]
/// Returns whether two metadata records identify the same file.
fn same_metadata_identity(
    left: &fs::Metadata,
    right: &fs::Metadata,
    _left_path: &Path,
    _right_path: &Path,
) -> bool {
    use std::os::unix::fs::MetadataExt;
    left.dev() == right.dev() && left.ino() == right.ino()
}

#[cfg(windows)]
fn same_metadata_identity(
    _left: &fs::Metadata,
    _right: &fs::Metadata,
    left_path: &Path,
    right_path: &Path,
) -> bool {
    same_file::is_same_file(left_path, right_path).unwrap_or(false)
}

#[cfg(not(any(unix, windows)))]
fn same_metadata_identity(
    _left: &fs::Metadata,
    _right: &fs::Metadata,
    left_path: &Path,
    right_path: &Path,
) -> bool {
    left_path.canonicalize().ok() == right_path.canonicalize().ok()
}

/// Returns whether a symbolic link points to the source.
#[cfg(not(windows))]
fn symlink_points_to(source: &Path, destination: &Path) -> bool {
    let Ok(target) = fs::read_link(destination) else {
        return false;
    };
    target.is_absolute() && source.canonicalize().is_ok_and(|source| source == target)
}

/// Returns whether a hard link would cross known volume boundaries.
#[cfg(not(windows))]
fn hardlink_definitely_crosses_volumes(source: &Path, destination: &Path) -> bool {
    let Some(parent) = nearest_existing_destination_ancestor(destination) else {
        return false;
    };
    volume_ids_differ(volume_id(source), volume_id(&parent))
}

/// Returns whether two known volume identifiers differ.
#[cfg(not(windows))]
const fn volume_ids_differ(source: Option<u64>, destination: Option<u64>) -> bool {
    match (source, destination) {
        (Some(source), Some(destination)) => source != destination,
        _ => false,
    }
}

/// Finds the nearest existing destination ancestor.
#[cfg(not(windows))]
fn nearest_existing_destination_ancestor(destination: &Path) -> Option<PathBuf> {
    let absolute = lexical_absolute(destination);
    let mut current = absolute.parent();
    while let Some(path) = current {
        if fs::metadata(path).is_ok() {
            return Some(path.to_path_buf());
        }
        current = path.parent();
    }
    None
}

#[cfg(unix)]
/// Returns the platform volume identifier for a path.
fn volume_id(path: &Path) -> Option<u64> {
    use std::os::unix::fs::MetadataExt;
    fs::metadata(path).ok().map(|metadata| metadata.dev())
}

#[cfg(not(any(unix, windows)))]
fn volume_id(_path: &Path) -> Option<u64> {
    None
}

/// Converts a path to lexical absolute form.
fn lexical_absolute(path: &Path) -> PathBuf {
    std::path::absolute(path).unwrap_or_else(|_| path.to_path_buf())
}

/// Builds a case-folded destination-collision key.
fn collision_key(path: &Path) -> PathBuf {
    let path = lexical_absolute(path);
    if cfg!(windows) || cfg!(target_os = "macos") {
        PathBuf::from(path.to_string_lossy().to_lowercase())
    } else {
        path
    }
}

crate::unit_tests!("mod.test.rs");
