//! Serializes paths as lossy display strings, including non-UTF Unix paths.

use serde::{Serialize, Serializer};
use std::path::{Path, PathBuf};

/// Serializes a path to its lossy display form.
pub fn serialize<S>(path: &Path, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    serializer.serialize_str(&path.to_string_lossy())
}

/// Serializes an optional path to its lossy display form.
pub fn serialize_option<S>(path: &Option<PathBuf>, serializer: S) -> Result<S::Ok, S::Error>
where
    S: Serializer,
{
    path.as_deref()
        .map(Path::to_string_lossy)
        .serialize(serializer)
}
