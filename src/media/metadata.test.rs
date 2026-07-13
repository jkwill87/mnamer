//! Verifies naming metadata behavior.

use super::*;

#[test]
fn provider_overlay_preserves_file_and_subtitle_fields() {
    let mut parsed = Metadata {
        media_type: MediaKind::Movie,
        container: Some("srt".into()),
        extension: Some("srt".into()),
        name: Some("Parsed".into()),
        quality: Some("1080p".into()),
        language_sub: Some("en".into()),
        subtitle_track: Some(2),
        subtitle_dispositions: vec![SubtitleDisposition::Forced],
        ..Metadata::default()
    };
    let provider = Metadata {
        media_type: MediaKind::Movie,
        name: Some("Canonical".into()),
        year: Some(2024),
        id_tmdb: Some("42".into()),
        ..Metadata::default()
    };

    parsed.overlay(&provider);

    assert_eq!(parsed.name.as_deref(), Some("Canonical"));
    assert_eq!(parsed.container.as_deref(), Some("srt"));
    assert_eq!(parsed.quality.as_deref(), Some("1080p"));
    assert_eq!(parsed.language_sub.as_deref(), Some("en"));
    assert_eq!(parsed.subtitle_track, Some(2));
    assert_eq!(parsed.subtitle_dispositions, [SubtitleDisposition::Forced]);
    assert_eq!(parsed.id_tmdb.as_deref(), Some("42"));
}
