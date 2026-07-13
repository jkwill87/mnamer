//! Verifies filesystem operation behavior.

#[cfg(unix)]
use super::*;

#[cfg(unix)]
#[test]
fn json_paths_use_lossy_display_strings_for_non_utf8_names() {
    use std::ffi::OsString;
    use std::os::unix::ffi::OsStringExt;

    let source = PathBuf::from(OsString::from_vec(b"rango-\xff.mkv".to_vec()));
    let operation = Operation::unresolved(0, source, Metadata::default());

    let value = serde_json::to_value(operation).unwrap();

    assert!(value["source"].as_str().unwrap().contains('\u{fffd}'));
}
