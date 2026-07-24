//! Verifies subtitle filename and directory semantics.

use super::*;

#[test]
fn parses_flat_language_disposition_and_numeric_track_metadata() {
    let subtitle = SubtitleFilename::parse(Path::new("Rango.2011.multi.2.forced.srt")).unwrap();

    assert_eq!(subtitle.format, MediaFormat::Srt);
    assert_eq!(subtitle.language, Some(LanguageTag::Multi));
    assert_eq!(subtitle.track, Some(2));
    assert_eq!(subtitle.dispositions, [SubtitleDisposition::Forced]);
    assert_eq!(subtitle.association_key(), Some("rango2011"));
    assert!(!subtitle.is_generic());
}

#[test]
fn resolves_only_qualified_subtitle_directory_chains() {
    let nested = subtitle_directory_context(Path::new(
        "The Woman King (2022)/Subs/English/Forced/track.srt",
    ));
    assert_eq!(
        nested.media_directory,
        Some(Path::new("The Woman King (2022)"))
    );
    assert_eq!(
        nested.language.map(|language| language.iso_639_1),
        Some("en")
    );
    assert_eq!(nested.dispositions, [SubtitleDisposition::Forced]);

    for (path, directory) in [
        ("Judge Dredd (1995)/Subs.en/track.srt", "Judge Dredd (1995)"),
        (
            "Oppenheimer (2023)/Subtitles-English/track.srt",
            "Oppenheimer (2023)",
        ),
        (
            "Filth (2013)/Subtitles-English-Forced/track.srt",
            "Filth (2013)",
        ),
        (
            "Death Proof (2007)/Subtitles (English)/track.srt",
            "Death Proof (2007)",
        ),
        (
            "Miss Congeniality (2000)/Subs [en]/track.srt",
            "Miss Congeniality (2000)",
        ),
    ] {
        let combined = subtitle_directory_context(Path::new(path));
        assert_eq!(
            combined.media_directory,
            Some(Path::new(directory)),
            "{path}"
        );
        assert_eq!(
            combined.language.map(|language| language.iso_639_1),
            Some("en"),
            "{path}"
        );
    }

    let combined = subtitle_directory_context(Path::new(
        "Dark Shadows (2012)/Subtitles-English-Forced/track.srt",
    ));
    assert_eq!(combined.dispositions, [SubtitleDisposition::Forced]);

    for (path, directory) in [
        (
            "Inception (2010)/Subs/English/1/track.srt",
            "Inception (2010)",
        ),
        (
            "Basic Instinct (1992)/Subs/1_English/track.srt",
            "Basic Instinct (1992)",
        ),
    ] {
        let numbered = subtitle_directory_context(Path::new(path));
        assert_eq!(
            numbered.media_directory,
            Some(Path::new(directory)),
            "{path}"
        );
        assert_eq!(numbered.track, Some(1), "{path}");
    }

    let unrelated = subtitle_directory_context(Path::new("Downloads 2024/Misc/English/track.srt"));
    assert_eq!(
        unrelated.media_directory,
        Some(Path::new("Downloads 2024/Misc"))
    );
    assert_eq!(
        unrelated.language.map(|language| language.iso_639_1),
        Some("en")
    );
    assert!(unrelated.dispositions.is_empty());
}
