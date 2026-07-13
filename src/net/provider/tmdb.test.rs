//! Verifies TMDb candidate searches and normalization.

use super::*;

#[test]
fn parses_year_prefix() {
    assert_eq!(parse_year("1999-10-15"), Some(1999));
    assert_eq!(parse_year("N/A"), None);
}
