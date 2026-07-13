//! Copies media files while preserving supported metadata.

use super::create_parent;
use std::fs::{self, File, FileTimes};
use std::io::{self, Read};
use std::path::Path;

/// Applies a copy operation.
pub(super) fn apply(source: &Path, destination: &Path, overwrite: bool) -> io::Result<()> {
    create_parent(destination)?;
    let metadata = fs::metadata(source)?;
    if !metadata.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "source is not a regular file",
        ));
    }

    let mut input = File::open(source)?;
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    let mut staged = tempfile::NamedTempFile::new_in(parent)?;
    io::copy(&mut input.by_ref(), staged.as_file_mut())?;

    let mut times = FileTimes::new();
    if let Ok(accessed) = metadata.accessed() {
        times = times.set_accessed(accessed);
    }
    if let Ok(modified) = metadata.modified() {
        times = times.set_modified(modified);
    }
    staged.as_file().set_times(times)?;
    staged.as_file().set_permissions(metadata.permissions())?;
    staged.as_file().sync_all()?;

    if overwrite {
        staged.persist(destination).map_err(|error| error.error)?;
    } else {
        staged
            .persist_noclobber(destination)
            .map_err(|error| error.error)?;
    }
    Ok(())
}
