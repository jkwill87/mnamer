//! Verifies OMDb candidate searches and normalization.

use super::*;

#[test]
fn year_matching_allows_five_year_variance() {
    assert!(year_matches(Some(2000), "1995"));
    assert!(!year_matches(Some(2000), "1994"));
    assert!(year_matches(None, "N/A"));
}
