//! Verifies TVDb candidate searches and normalization.

use super::*;

#[test]
fn accepts_only_tvdb_v3_language_codes() {
    for language in ["en", "fi", "hu", "nl", "no", "pl"] {
        assert!(
            supports_language(Language::from_identifier(language).unwrap()),
            "{language}"
        );
    }
    assert!(!supports_language(Language::from_identifier("uk").unwrap()));
}
