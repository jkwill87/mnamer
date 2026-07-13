//! Creates hard links for planned media targets.

use super::create_parent;
use std::fs;
use std::io;
use std::path::Path;

/// Applies a hard-link operation.
pub(super) fn apply(source: &Path, destination: &Path) -> io::Result<()> {
    if !fs::metadata(source)?.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "source is not a regular file",
        ));
    }
    create_parent(destination)?;
    fs::hard_link(source, destination)
}
