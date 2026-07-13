//! Discovers execution targets deterministically.

use crate::media::MediaFormat;
use globset::{GlobBuilder, GlobSet, GlobSetBuilder};
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Options controlling input discovery.
#[derive(Debug, Clone)]
pub struct DiscoveryOptions {
    /// Whether directories are traversed recursively.
    pub recursive: bool,
    /// Accepted extensions without leading dots.
    pub extensions: Vec<String>,
    /// Case-insensitive glob patterns matched against full paths.
    pub ignore: Vec<String>,
}

impl Default for DiscoveryOptions {
    fn default() -> Self {
        Self {
            recursive: false,
            extensions: ["avi", "m4v", "mp4", "mkv", "ts", "wmv"]
                .into_iter()
                .chain(
                    MediaFormat::ALL
                        .into_iter()
                        .filter(|format| format.is_subtitle())
                        .map(MediaFormat::extension),
                )
                .map(str::to_owned)
                .collect(),
            ignore: vec!["**/*sample*".into()],
        }
    }
}

/// A path-specific discovery failure.
#[derive(Debug, Clone, Serialize)]
pub struct DiscoveryFailure {
    /// Path that could not be discovered or read.
    #[serde(serialize_with = "crate::cli::output::path::serialize")]
    pub path: PathBuf,
    /// Human-readable reason.
    pub message: String,
}

/// Deterministic discovery results and non-fatal failures.
#[derive(Debug, Default)]
pub struct DiscoveryResult {
    /// Sorted, deduplicated media files.
    pub files: Vec<PathBuf>,
    /// Inputs or directory entries that could not be read.
    pub failures: Vec<DiscoveryFailure>,
}

/// An invalid discovery configuration.
#[derive(Debug, thiserror::Error)]
pub enum DiscoveryConfigError {
    /// A configured glob could not be compiled.
    #[error("invalid ignore glob {pattern:?}: {source}")]
    InvalidGlob {
        /// Original glob pattern.
        pattern: String,
        /// Glob parser error.
        source: globset::Error,
    },
}

/// Discovers all accepted files beneath the provided roots.
pub fn discover(
    roots: &[PathBuf],
    options: &DiscoveryOptions,
) -> Result<DiscoveryResult, DiscoveryConfigError> {
    let ignore = build_ignore_set(&options.ignore)?;
    let extensions = options
        .extensions
        .iter()
        .map(|value| value.trim_start_matches('.').to_ascii_lowercase())
        .collect::<BTreeSet<_>>();
    let mut files = BTreeMap::new();
    let mut failures = Vec::new();

    for root in roots {
        let metadata = match fs::symlink_metadata(root) {
            Ok(metadata) => metadata,
            Err(error) => {
                failures.push(DiscoveryFailure {
                    path: root.clone(),
                    message: if error.kind() == std::io::ErrorKind::NotFound {
                        "path does not exist".into()
                    } else {
                        error.to_string()
                    },
                });
                continue;
            }
        };
        if metadata.file_type().is_symlink() {
            failures.push(DiscoveryFailure {
                path: root.clone(),
                message: "symbolic links are not processed".into(),
            });
            continue;
        }
        if metadata.is_file() {
            insert_if_accepted(root, &extensions, &ignore, &mut files);
            continue;
        }
        if !metadata.is_dir() {
            failures.push(DiscoveryFailure {
                path: root.clone(),
                message: "path is not a regular file or directory".into(),
            });
            continue;
        }

        let mut walker = WalkDir::new(root).follow_links(false).min_depth(1);
        if !options.recursive {
            walker = walker.max_depth(1);
        }
        for entry in walker {
            match entry {
                Ok(entry) if entry.file_type().is_file() => {
                    insert_if_accepted(entry.path(), &extensions, &ignore, &mut files);
                }
                Ok(_) => {}
                Err(error) => failures.push(DiscoveryFailure {
                    path: error.path().map_or_else(|| root.clone(), Path::to_path_buf),
                    message: error.to_string(),
                }),
            }
        }
    }

    Ok(DiscoveryResult {
        files: files.into_values().collect(),
        failures,
    })
}

/// Compiles configured ignore patterns.
fn build_ignore_set(patterns: &[String]) -> Result<GlobSet, DiscoveryConfigError> {
    let mut builder = GlobSetBuilder::new();
    for pattern in patterns {
        let glob = GlobBuilder::new(pattern)
            .case_insensitive(true)
            .build()
            .map_err(|source| DiscoveryConfigError::InvalidGlob {
                pattern: pattern.clone(),
                source,
            })?;
        builder.add(glob);
    }
    builder
        .build()
        .map_err(|source| DiscoveryConfigError::InvalidGlob {
            pattern: "<glob set>".into(),
            source,
        })
}

/// Adds a discovered path when it satisfies all filters.
fn insert_if_accepted(
    path: &Path,
    extensions: &BTreeSet<String>,
    ignore: &GlobSet,
    files: &mut BTreeMap<PathBuf, PathBuf>,
) {
    if ignore.is_match(path) {
        return;
    }
    let Some(extension) = path.extension().and_then(|value| value.to_str()) else {
        return;
    };
    if !extensions.is_empty() && !extensions.contains(&extension.to_ascii_lowercase()) {
        return;
    }
    let source = std::path::absolute(path).unwrap_or_else(|_| path.to_path_buf());
    let identity = path.canonicalize().unwrap_or_else(|_| source.clone());
    files.entry(identity).or_insert(source);
}

crate::unit_tests!("discovery.test.rs");
