//! Moves media files to planned destinations.

use super::{copy, create_parent, same_lexical_path, same_regular_file};
use std::fs;
use std::io;
use std::path::Path;

/// Applies a move operation.
pub(super) fn apply(source: &Path, destination: &Path, overwrite: bool) -> io::Result<()> {
    create_parent(destination)?;
    if same_lexical_path(source, destination) {
        return Ok(());
    }
    if same_regular_file(source, destination) {
        return rename_through_temporary_path(source, destination);
    }

    if overwrite {
        match fs::rename(source, destination) {
            Ok(()) => return Ok(()),
            Err(error)
                if matches!(
                    error.kind(),
                    io::ErrorKind::CrossesDevices | io::ErrorKind::AlreadyExists
                ) => {}
            Err(error) => return Err(error),
        }
    } else {
        match fs::hard_link(source, destination) {
            Ok(()) => return fs::remove_file(source),
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                return Err(io::Error::new(
                    io::ErrorKind::AlreadyExists,
                    "destination already exists",
                ));
            }
            Err(_) => {}
        }
    }

    copy_then_remove(source, destination, overwrite)
}

/// Completes the cross-filesystem fallback using destination-local staging.
pub(super) fn copy_then_remove(
    source: &Path,
    destination: &Path,
    overwrite: bool,
) -> io::Result<()> {
    copy::apply(source, destination, overwrite)?;
    fs::remove_file(source)
}

/// Performs a case-only rename through a temporary path.
fn rename_through_temporary_path(source: &Path, destination: &Path) -> io::Result<()> {
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    let temporary_directory = tempfile::Builder::new()
        .prefix(".mnamer-case-")
        .tempdir_in(parent)?;
    let staged = temporary_directory.path().join("source");
    fs::rename(source, &staged)?;
    match fs::rename(&staged, destination) {
        Ok(()) => Ok(()),
        Err(error) => match fs::rename(&staged, source) {
            Ok(()) => Err(error),
            Err(restore_error) => {
                let staged_display = staged.display().to_string();
                let _ = temporary_directory.keep();
                Err(io::Error::other(format!(
                    "case-only rename failed ({error}) and source restoration failed ({restore_error}); staged file remains at {staged_display}"
                )))
            }
        },
    }
}
