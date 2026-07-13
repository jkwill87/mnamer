//! Verifies conversion from inspected tags to naming metadata.

use super::*;
use crate::media::SubtitleDisposition;
use std::fs;

fn riff_chunk(kind: &[u8; 4], payload: &[u8]) -> Vec<u8> {
    let mut output = kind.to_vec();
    output.extend_from_slice(&u32::try_from(payload.len()).unwrap().to_le_bytes());
    output.extend_from_slice(payload);
    if payload.len() & 1 != 0 {
        output.push(0);
    }
    output
}

fn technical_avi_fixture() -> Vec<u8> {
    let mut avih = vec![0; 40];
    avih[..4].copy_from_slice(&33_333_u32.to_le_bytes());
    avih[16..20].copy_from_slice(&300_u32.to_le_bytes());
    avih[32..36].copy_from_slice(&1920_u32.to_le_bytes());
    avih[36..40].copy_from_slice(&1080_u32.to_le_bytes());

    let mut video_header = vec![0; 36];
    video_header[..4].copy_from_slice(b"vids");
    video_header[4..8].copy_from_slice(b"H265");
    let mut video_format = vec![0; 40];
    video_format[..4].copy_from_slice(&40_u32.to_le_bytes());
    video_format[4..8].copy_from_slice(&1920_i32.to_le_bytes());
    video_format[8..12].copy_from_slice(&1080_i32.to_le_bytes());
    video_format[16..20].copy_from_slice(b"H265");
    let mut video = b"strl".to_vec();
    video.extend_from_slice(&riff_chunk(b"strh", &video_header));
    video.extend_from_slice(&riff_chunk(b"strf", &video_format));

    let mut audio_header = vec![0; 36];
    audio_header[..4].copy_from_slice(b"auds");
    let mut audio_format = vec![0; 16];
    audio_format[..2].copy_from_slice(&0x0161_u16.to_le_bytes());
    audio_format[2..4].copy_from_slice(&6_u16.to_le_bytes());
    let mut audio = b"strl".to_vec();
    audio.extend_from_slice(&riff_chunk(b"strh", &audio_header));
    audio.extend_from_slice(&riff_chunk(b"strf", &audio_format));

    let mut hdrl = b"hdrl".to_vec();
    hdrl.extend_from_slice(&riff_chunk(b"avih", &avih));
    hdrl.extend_from_slice(&riff_chunk(b"LIST", &video));
    hdrl.extend_from_slice(&riff_chunk(b"LIST", &audio));
    let hdrl = riff_chunk(b"LIST", &hdrl);
    let mut output = b"RIFF".to_vec();
    output.extend_from_slice(&u32::try_from(hdrl.len() + 4).unwrap().to_le_bytes());
    output.extend_from_slice(b"AVI ");
    output.extend_from_slice(&hdrl);
    output
}

#[test]
fn file_content_replaces_conflicting_filename_quality_by_category() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("Example.2024.720p.H264.AAC.mkv");
    fs::write(&path, technical_avi_fixture()).unwrap();

    let inspected = Metadata::inspect(&path, Some(MediaKind::Movie));
    let quality = inspected.quality.as_deref().unwrap();
    assert_eq!(inspected.container.as_deref(), Some("avi"));
    assert!(quality.contains("1080p"), "{quality}");
    assert!(quality.contains("h265"), "{quality}");
    assert!(quality.contains("dolby_digital_plus"), "{quality}");
    assert!(quality.contains("5.1"), "{quality}");
    assert!(!quality.contains("720p"), "{quality}");
    assert!(!quality.contains("h264"), "{quality}");
    assert!(
        !quality.split_whitespace().any(|value| value == "aac"),
        "{quality}"
    );

    let filename_only = Metadata::inspect_with_file_content(&path, Some(MediaKind::Movie), false);
    let quality = filename_only.quality.as_deref().unwrap();
    assert_eq!(filename_only.container.as_deref(), Some("mkv"));
    assert!(quality.contains("720p"), "{quality}");
    assert!(quality.contains("h264"), "{quality}");
    assert!(
        quality.split_whitespace().any(|value| value == "aac"),
        "{quality}"
    );
}

#[test]
fn detects_missing_subtitle_languages_from_text_content() {
    let directory = tempfile::tempdir().unwrap();
    let french = "Bonjour tout le monde. Nous attendons le train du matin à la gare. Cette histoire continue avec plusieurs phrases clairement écrites en français.";
    let fixtures = [
        (
            "Arrival.2016.srt",
            format!("1\n00:00:01,000 --> 00:00:04,000\n{french}\n"),
        ),
        (
            "Arrival.2016.ass",
            format!(
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{french}\n"
            ),
        ),
        (
            "Arrival.2016.ssa",
            format!(
                "[Events]\nFormat: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: Marked=0,0:00:01.00,0:00:04.00,Default,,0,0,0,,{french}\n"
            ),
        ),
        (
            "Arrival.2016.vtt",
            format!("WEBVTT\n\n00:01.000 --> 00:04.000\n{french}\n"),
        ),
        ("Arrival.2016.sub", format!("{{1}}{{100}}{french}\n")),
    ];

    for (name, contents) in fixtures {
        let path = directory.path().join(name);
        fs::write(&path, contents).unwrap();
        assert_eq!(
            Metadata::inspect(&path, Some(MediaKind::Movie))
                .language_sub
                .as_deref(),
            Some("fr"),
            "{name}"
        );
    }
}

#[test]
fn explicit_subtitle_language_precedes_content_detection() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("Arrival.2016.en.srt");
    fs::write(
        &path,
        "1\n00:00:01,000 --> 00:00:04,000\nBonjour tout le monde. Nous attendons le train du matin à la gare.\n",
    )
    .unwrap();

    let metadata = Metadata::inspect(&path, Some(MediaKind::Movie));
    assert_eq!(metadata.language_sub.as_deref(), Some("en"));
}

#[test]
fn disabled_or_non_text_inspection_leaves_subtitle_language_unset() {
    let directory = tempfile::tempdir().unwrap();
    let text = "Bonjour tout le monde. Nous attendons le train du matin à la gare.";

    let disabled = directory.path().join("Arrival.2016.srt");
    fs::write(&disabled, text).unwrap();
    assert_eq!(
        Metadata::inspect_with_file_content(&disabled, Some(MediaKind::Movie), false).language_sub,
        None
    );

    let index = directory.path().join("Arrival.2016.idx");
    fs::write(&index, text).unwrap();
    assert_eq!(
        Metadata::inspect(&index, Some(MediaKind::Movie)).language_sub,
        None
    );

    let binary_sub = directory.path().join("Arrival.2016.sub");
    fs::write(&binary_sub, [0x00, 0x00, 0x01, 0xba, 0xff, 0xfe]).unwrap();
    assert_eq!(
        Metadata::inspect(&binary_sub, Some(MediaKind::Movie)).language_sub,
        None
    );
}

#[test]
fn inspects_movie_and_episode_metadata() {
    let movie = Metadata::inspect(
        Path::new("The.Goonies.1985.1080p.BluRay.x264-FLAME.mkv"),
        None,
    );
    assert_eq!(movie.media_type, MediaKind::Movie);
    assert_eq!(movie.name.as_deref(), Some("The Goonies"));
    assert_eq!(movie.year, Some(1985));
    assert_eq!(movie.group.as_deref(), Some("FLAME"));

    let episode = Metadata::inspect(
        Path::new("Severance.S01E02.Half.Loop.2160p.WEB.H265-FLAME.mkv"),
        None,
    );
    assert_eq!(episode.media_type, MediaKind::Episode);
    assert_eq!(episode.series.as_deref(), Some("Severance"));
    assert_eq!(episode.season, Some(1));
    assert_eq!(episode.episode, Some(2));
}

#[test]
fn alternative_series_titles_are_preserved_in_provider_metadata() {
    let anime = Metadata::inspect(
        Path::new("[HorribleSubs].Garo.-.Vanishing.Line.-.11.[1080p].mkv"),
        None,
    );
    assert_eq!(anime.media_type, MediaKind::Episode);
    assert_eq!(anime.series.as_deref(), Some("Garo - Vanishing Line"));
    assert_eq!(anime.episode, Some(11));
    assert_eq!(anime.group.as_deref(), Some("HORRIBLESUBS"));

    let episode = Metadata::inspect(
        Path::new("Kaamelott - Livre V - Ep 23 - Le Forfait.avi"),
        None,
    );
    assert_eq!(episode.series.as_deref(), Some("Kaamelott - Livre V"));
    assert_eq!(episode.episode, Some(23));
    assert_eq!(episode.title.as_deref(), Some("Le Forfait"));
}

#[test]
fn detects_language_and_retains_dispositions_without_polluting_title() {
    let metadata = Metadata::inspect(
        Path::new("The.Croods.A.New.Age.2020.en.forced.srt"),
        Some(MediaKind::Movie),
    );

    assert_eq!(metadata.name.as_deref(), Some("The Croods A New Age"));
    assert_eq!(metadata.year, Some(2020));
    assert_eq!(metadata.language_sub.as_deref(), Some("en"));
    assert_eq!(
        metadata.subtitle_dispositions,
        [SubtitleDisposition::Forced]
    );
    assert_eq!(
        serde_json::to_value(&metadata).unwrap()["subtitle_dispositions"],
        serde_json::json!(["forced"])
    );
}

#[test]
fn ambiguous_short_titles_override_inspector_language_inference() {
    for (path, name, language, dispositions) in [
        ("It.srt", "It", None, vec![]),
        (
            "Up.forced.srt",
            "Up",
            None,
            vec![SubtitleDisposition::Forced],
        ),
        ("Her.en.srt", "Her", Some("en"), vec![]),
    ] {
        let metadata = Metadata::inspect(Path::new(path), Some(MediaKind::Movie));
        assert_eq!(metadata.name.as_deref(), Some(name), "{path}");
        assert_eq!(metadata.language_sub.as_deref(), language, "{path}");
        assert_eq!(metadata.subtitle_dispositions, dispositions, "{path}");
    }
}

#[test]
fn uses_strong_ancestor_context_for_generic_nested_and_random_subtitles() {
    for (path, name, year) in [
        ("Saw (2004)/Eng.srt", "Saw", 2004),
        ("Closer (2004)/random.idx", "Closer", 2004),
        ("Fresh (2022)/Subs/English.sub", "Fresh", 2022),
        ("Up (2009)/English/track.srt", "Up", 2009),
        ("Cars (2006)/Subs/English/UTF8/track.srt", "Cars", 2006),
    ] {
        let metadata = Metadata::inspect(Path::new(path), None);
        assert_eq!(metadata.media_type, MediaKind::Movie, "{path}");
        assert_eq!(metadata.name.as_deref(), Some(name), "{path}");
        assert_eq!(metadata.year, Some(year), "{path}");
    }
}

#[test]
fn resolves_deep_language_and_disposition_subtitle_directories() {
    let metadata = Metadata::inspect(
        Path::new("Anora (2024)/Subs/English/Forced/track.srt"),
        None,
    );

    assert_eq!(metadata.media_type, MediaKind::Movie);
    assert_eq!(metadata.name.as_deref(), Some("Anora"));
    assert_eq!(metadata.year, Some(2024));
    assert_eq!(metadata.language_sub.as_deref(), Some("en"));
    assert_eq!(
        metadata.subtitle_dispositions,
        [SubtitleDisposition::Forced]
    );
}

#[test]
fn retains_numeric_tracks_from_filenames_and_subtitle_directories() {
    for (path, name) in [
        ("Deadpool (2016)/Deadpool.2016.en.2.srt", "Deadpool"),
        ("Thor (2011)/Subs/English/2/track.srt", "Thor"),
    ] {
        let metadata = Metadata::inspect(Path::new(path), None);
        assert_eq!(metadata.name.as_deref(), Some(name), "{path}");
        assert_eq!(metadata.language_sub.as_deref(), Some("en"), "{path}");
        assert_eq!(metadata.subtitle_track, Some(2), "{path}");
    }
}

#[test]
fn qualifier_first_generic_names_use_strong_ancestor_identity() {
    for (directory, name, year, disposition) in [
        (
            "Blood Simple (1985)",
            "Blood Simple",
            1985,
            SubtitleDisposition::Forced,
        ),
        ("Con Air (1997)", "Con Air", 1997, SubtitleDisposition::Sdh),
        (
            "Game Night (2018)",
            "Game Night",
            2018,
            SubtitleDisposition::Commentary,
        ),
    ] {
        let filename = match disposition {
            SubtitleDisposition::Forced => "forced.eng.srt",
            SubtitleDisposition::Sdh => "sdh.eng.srt",
            SubtitleDisposition::Commentary => "commentary.eng.srt",
        };
        let path = format!("{directory}/{filename}");
        let metadata = Metadata::inspect(Path::new(&path), None);
        assert_eq!(metadata.name.as_deref(), Some(name), "{path}");
        assert_eq!(metadata.year, Some(year), "{path}");
        assert_eq!(metadata.language_sub.as_deref(), Some("en"), "{path}");
        assert_eq!(metadata.subtitle_dispositions, [disposition], "{path}");
    }
}

#[test]
fn does_not_inherit_from_unrelated_distant_year_bearing_ancestors() {
    let metadata = Metadata::inspect(
        Path::new("Downloads 2024/Misc/Subs/English.srt"),
        Some(MediaKind::Movie),
    );

    assert_eq!(metadata.year, None);
    assert_ne!(metadata.name.as_deref(), Some("Downloads"));
}

#[test]
fn supports_all_subtitle_containers_understood_by_mediakit() {
    for path in [
        "Old.Yeller.1957.en.srt",
        "Sonic.the.Hedgehog.2.2022.en.idx",
        "Old.School.2003.en.sub",
        "Superman.2025.en.ass",
        "Atlantis.The.Lost.Empire.2001.en.ssa",
        "RoboCop.2.1990.en.vtt",
    ] {
        let metadata = Metadata::inspect(Path::new(path), Some(MediaKind::Movie));
        assert!(metadata.is_subtitle(), "{path}");
        assert_eq!(metadata.language_sub.as_deref(), Some("en"), "{path}");
    }
}
