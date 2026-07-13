//! Verifies destination-template rendering and path safety.

use super::*;

#[test]
fn renders_default_movie_destination() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("The Big Lebowski".into()),
        year: Some(1998),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/The.Big.Lebowski.1998.1080p.BluRay.x264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(actual, PathBuf::from("/tmp/The Big Lebowski (1998).mkv"));
}

#[test]
fn renders_padded_episode_and_removes_empty_title() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Episode,
        extension: Some("mkv".into()),
        series: Some("King of the Hill".into()),
        season: Some(14),
        episode: Some(2),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/King.of.the.Hill.S14E02.The.Beer.Story.1080p.WEB.H264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(actual, PathBuf::from("/tmp/King of the Hill - S14E02.mkv"));
}

#[test]
fn preserves_absolute_literal_directories() {
    let options = FormatOptions {
        movie_directory: Some(PathBuf::from("/Media Library/{{ name | first }}")),
        lowercase: true,
        ..FormatOptions::default()
    };
    let formatter = DestinationFormatter::new(options).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("Teen Wolf".into()),
        year: Some(1985),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("Teen.Wolf.1985.1080p.BluRay.x264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/Media Library/t/teen wolf (1985).mkv")
    );
}

#[test]
fn inserts_subtitle_language_into_extension() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("srt".into()),
        name: Some("The Indian in the Cupboard".into()),
        year: Some(1995),
        language_sub: Some("en".into()),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/The.Indian.in.the.Cupboard.1995.en.srt"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/tmp/The Indian in the Cupboard (1995).en.srt")
    );
}

#[test]
fn maps_three_letter_subtitle_language_to_two_letters() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Episode,
        extension: Some("srt".into()),
        series: Some("slow horses".into()),
        season: Some(2),
        episode: Some(3),
        title: Some("drinking games".into()),
        language_sub: Some("eng".into()),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/Slow.Horses.S02E03.Drinking.Games.en.srt"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/tmp/Slow Horses - S02E03 - Drinking Games.en.srt")
    );
}

#[test]
fn regional_subtitle_tags_collapse_to_two_letter_destinations() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata::inspect(
        Path::new("Sincerely.Louis.C.K.2020.pt-BR.srt"),
        Some(MediaKind::Movie),
    );

    let actual = formatter
        .destination(
            Path::new("/tmp/Sincerely.Louis.C.K.2020.pt-BR.srt"),
            &metadata,
        )
        .unwrap();

    assert_eq!(
        actual,
        PathBuf::from("/tmp/Sincerely Louis C K (2020).pt.srt")
    );
}

#[test]
fn commentary_track_is_retained_in_the_destination() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata::inspect(
        Path::new("Louis.C.K.Hilarious.2010.en.commentary2.srt"),
        Some(MediaKind::Movie),
    );

    let actual = formatter
        .destination(
            Path::new("/tmp/Louis.C.K.Hilarious.2010.en.commentary2.srt"),
            &metadata,
        )
        .unwrap();

    assert_eq!(
        actual,
        PathBuf::from("/tmp/Louis C K Hilarious (2010).en.2.commentary.srt")
    );
}

#[test]
fn preserves_dispositions_and_keeps_regular_and_forced_destinations_distinct() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let regular = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("srt".into()),
        name: Some("West Side Story".into()),
        year: Some(2021),
        language_sub: Some("eng".into()),
        ..Metadata::default()
    };
    let forced = Metadata {
        subtitle_dispositions: vec![crate::media::SubtitleDisposition::Forced],
        ..regular.clone()
    };

    let regular = formatter
        .destination(Path::new("/tmp/West.Side.Story.2021.en.srt"), &regular)
        .unwrap();
    let forced = formatter
        .destination(
            Path::new("/tmp/West.Side.Story.2021.en.forced.srt"),
            &forced,
        )
        .unwrap();

    assert_eq!(regular, PathBuf::from("/tmp/West Side Story (2021).en.srt"));
    assert_eq!(
        forced,
        PathBuf::from("/tmp/West Side Story (2021).en.forced.srt")
    );
    assert_ne!(regular, forced);
}

#[test]
fn preserves_numeric_tracks_and_keeps_parallel_subtitles_distinct() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let first = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("srt".into()),
        name: Some("Brave".into()),
        year: Some(2012),
        language_sub: Some("en".into()),
        subtitle_track: Some(1),
        ..Metadata::default()
    };
    let second = Metadata {
        subtitle_track: Some(2),
        ..first.clone()
    };

    let first = formatter
        .destination(Path::new("/tmp/Brave.2012.en.1.srt"), &first)
        .unwrap();
    let second = formatter
        .destination(Path::new("/tmp/Brave.2012.en.2.srt"), &second)
        .unwrap();

    assert_eq!(first, PathBuf::from("/tmp/Brave (2012).en.1.srt"));
    assert_eq!(second, PathBuf::from("/tmp/Brave (2012).en.2.srt"));
    assert_ne!(first, second);
}

#[test]
fn formats_every_supported_subtitle_container() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    for (extension, name, year) in [
        ("srt", "Inside Out 2", 2024),
        ("idx", "The Nun", 2018),
        ("sub", "Free Guy", 2021),
        ("ass", "Mandy", 2018),
        ("ssa", "Red Rocket", 2021),
        ("vtt", "Saint Maud", 2020),
    ] {
        let metadata = Metadata {
            media_type: MediaKind::Movie,
            extension: Some(extension.into()),
            name: Some(name.into()),
            year: Some(year),
            language_sub: Some("English".into()),
            ..Metadata::default()
        };
        let destination = formatter
            .destination(
                Path::new(&format!("/tmp/{}.en.{extension}", name.replace(' ', "."))),
                &metadata,
            )
            .unwrap();

        assert_eq!(
            destination.file_name().and_then(|name| name.to_str()),
            Some(format!("{name} ({year}).en.{extension}").as_str()),
            "{extension}"
        );
    }
}

#[test]
fn title_cases_metadata_and_replaces_metadata_slashes() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("john wick chapter 3 / parabellum".into()),
        year: Some(2019),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/John.Wick.Chapter.3.Parabellum.2019.2160p.BluRay.x265-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/tmp/John Wick Chapter 3 - Parabellum (2019).mkv")
    );
}

#[test]
fn title_case_recognizes_additional_minor_words() {
    for word in ["en", "if", "per", "vs"] {
        assert_eq!(
            title_case(&format!("alpha {word} omega")),
            format!("Alpha {word} Omega"),
            "{word}"
        );
    }
}

#[test]
fn title_case_recognizes_additional_initialisms_and_roman_numerals() {
    for word in [
        "a24", "abc", "ac", "ai", "aids", "amc", "cbs", "cnn", "diy", "dna", "dvd", "eu", "gps",
        "hbo", "hd", "hiv", "imax", "irs", "lgbt", "lgbtq", "mcu", "mls", "nasa", "nbc", "ncaa",
        "nsa", "nypd", "pbs", "sos", "swat", "tbs", "uhd", "vhs", "vr", "wnba", "xi", "xii",
        "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx",
    ] {
        assert_eq!(
            title_case(&format!("the {word} story")),
            format!("The {} Story", word.to_uppercase()),
            "{word}"
        );
    }
}

#[test]
fn sanitizes_illegal_characters_and_collapses_whitespace() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("dungeons & dragons:  honor * among? thieves".into()),
        year: Some(2023),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new(
                "/tmp/Dungeons.and.Dragons.Honor.Among.Thieves.2023.2160p.BluRay.x265-FLAME.mkv",
            ),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/tmp/Dungeons & Dragons Honor Among Thieves (2023).mkv")
    );
}

#[test]
fn transforms_format_emitted_directory_components() {
    let options = FormatOptions {
        movie_format: "{{ name }}/{{ name }} ({{ year }}).{{ extension }}".into(),
        lowercase: true,
        ..FormatOptions::default()
    };
    let formatter = DestinationFormatter::new(options).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("The Road to El Dorado".into()),
        year: Some(2000),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/The.Road.to.El.Dorado.2000.1080p.BluRay.x264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/tmp/the road to el dorado/the road to el dorado (2000).mkv")
    );
}

#[test]
fn transforms_relative_directory_literals_in_scene_mode() {
    let options = FormatOptions {
        movie_directory: Some(PathBuf::from("Movie Library/{{ name }}")),
        scene: true,
        ..FormatOptions::default()
    };
    let formatter = DestinationFormatter::new(options).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("Flushed Away".into()),
        year: Some(2006),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("Flushed.Away.2006.1080p.BluRay.x264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        std::path::absolute("movie.library/flushed.away/flushed.away.2006.mkv").unwrap()
    );
}

#[test]
fn preserves_absolute_literal_directory_text_in_scene_mode() {
    let options = FormatOptions {
        movie_directory: Some(PathBuf::from("/Media  Library/Movies")),
        scene: true,
        ..FormatOptions::default()
    };
    let formatter = DestinationFormatter::new(options).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("Employee of the Month".into()),
        year: Some(2006),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("Employee.of.the.Month.2006.1080p.BluRay.x264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(
        actual,
        PathBuf::from("/Media  Library/Movies/employee.of.the.month.2006.mkv")
    );
}

#[test]
fn makes_windows_device_names_safe() {
    let options = FormatOptions {
        movie_format: "{{ name }}.{{ extension }}".into(),
        ..FormatOptions::default()
    };
    let formatter = DestinationFormatter::new(options).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Movie,
        extension: Some("mkv".into()),
        name: Some("con".into()),
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/Con.Air.1997.1080p.BluRay.x264-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(actual, PathBuf::from("/tmp/_Con.mkv"));
}

#[test]
fn exposes_multi_episode_values_to_templates() {
    let options = FormatOptions {
        episode_format: "{{ series }} - E{{ episodes.1 | pad: 2 }}.{{ extension }}".into(),
        ..FormatOptions::default()
    };
    let formatter = DestinationFormatter::new(options).unwrap();
    let metadata = Metadata {
        media_type: MediaKind::Episode,
        extension: Some("mkv".into()),
        series: Some("Futurama".into()),
        episodes: vec![2, 3],
        ..Metadata::default()
    };
    let actual = formatter
        .destination(
            Path::new("/tmp/Futurama.S09E01E02.2160p.WEB.H265-FLAME.mkv"),
            &metadata,
        )
        .unwrap();
    assert_eq!(actual, PathBuf::from("/tmp/Futurama - E03.mkv"));
}

#[test]
fn validates_all_templates_during_construction() {
    let options = FormatOptions {
        movie_format: "{{ name".into(),
        ..FormatOptions::default()
    };
    assert!(matches!(
        DestinationFormatter::new(options),
        Err(FormatError::Template(_))
    ));

    let options = FormatOptions {
        movie_directory: Some(PathBuf::from("Movies/{{ name")),
        ..FormatOptions::default()
    };
    assert!(matches!(
        DestinationFormatter::new(options),
        Err(FormatError::Template(_))
    ));
}

#[test]
fn rejects_unknown_template_functions_during_construction() {
    let options = FormatOptions {
        movie_format: "{{ name | totally_unknown }}.{{ extension }}".into(),
        ..FormatOptions::default()
    };

    assert!(matches!(
        DestinationFormatter::new(options),
        Err(FormatError::Template(_))
    ));
}

#[test]
fn refuses_unknown_media() {
    let formatter = DestinationFormatter::new(FormatOptions::default()).unwrap();
    let metadata = Metadata::default();
    assert!(matches!(
        formatter.destination(
            Path::new("/tmp/Return.to.Silent.Hill.2026.2160p.WEB.H265-FLAME.mkv"),
            &metadata
        ),
        Err(FormatError::UnknownMedia)
    ));
}
