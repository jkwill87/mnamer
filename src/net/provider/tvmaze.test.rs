//! Verifies TVmaze candidate searches and normalization.

use super::*;

#[test]
fn strips_html_from_episode_summaries() {
    assert_eq!(strip_html("<p>Hello <b>world</b></p>"), "Hello world");
}
