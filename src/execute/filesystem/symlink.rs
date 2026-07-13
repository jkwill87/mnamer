//! Creates symbolic links for planned media targets.

use super::create_parent;
use std::fs;
use std::io;
use std::path::Path;

/// Applies a symbolic-link operation.
pub(super) fn apply(source: &Path, destination: &Path) -> io::Result<()> {
    let target = source.canonicalize()?;
    if !fs::metadata(&target)?.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "source is not a regular file",
        ));
    }
    create_parent(destination)?;
    if !fs::metadata(source)?.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "source is not a regular file",
        ));
    }
    create_file_symlink(&target, destination)
}

#[cfg(unix)]
/// Creates a platform-appropriate file symbolic link.
fn create_file_symlink(target: &Path, destination: &Path) -> io::Result<()> {
    std::os::unix::fs::symlink(target, destination)
}

#[cfg(not(any(unix, windows)))]
fn create_file_symlink(_target: &Path, _destination: &Path) -> io::Result<()> {
    Err(io::Error::new(
        io::ErrorKind::Unsupported,
        "file symlinks are not supported on this platform",
    ))
}
