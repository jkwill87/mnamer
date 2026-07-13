//! Verifies interactive prompt behavior.

use super::*;
use crate::media::MediaKind;
use crate::net::provider::ProviderKind;

#[test]
fn candidate_labels_focus_on_media_identity() {
    let candidate = Candidate {
        provider: ProviderKind::Tvmaze,
        metadata: Metadata {
            media_type: MediaKind::Episode,
            series: Some("The Expanse".into()),
            season: Some(1),
            episode: Some(2),
            title: Some("The Big Empty".into()),
            ..Metadata::default()
        },
        score: Some(1.0),
    };

    assert_eq!(
        candidate_label(&candidate),
        "The Expanse S01E02 - The Big Empty"
    );
}

#[test]
fn filename_guess_labels_are_explicit() {
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        title: Some("Mickey 17".into()),
        year: Some(2025),
        ..Metadata::default()
    };

    assert_eq!(
        guess_label(&metadata),
        "Use filename guess: Mickey 17 (2025)"
    );
}

#[test]
fn processing_labels_match_python_style_with_binary_sizes() {
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        file_size: Some(16 * 1024 * 1024 * 1024),
        extension: Some("mkv".into()),
        ..Metadata::default()
    };

    assert_eq!(
        processing_label(
            Path::new("/media/A Nightmare on Elm Street Part 2 (1985).mkv"),
            &metadata
        ),
        "Processing Movie \"A Nightmare on Elm Street Part 2 (1985).mkv\" (16.00GB)"
    );
}

#[test]
fn processing_labels_identify_subtitles() {
    let metadata = Metadata {
        media_type: MediaKind::Episode,
        extension: Some("srt".into()),
        ..Metadata::default()
    };

    assert_eq!(
        processing_label(Path::new("/media/The Expanse S01E01.en.srt"), &metadata),
        "Processing Episode Subtitle \"The Expanse S01E01.en.srt\" (unknown size)"
    );
}
