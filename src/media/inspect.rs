//! Converts media inspection results into naming metadata.

use super::subtitle::{detect_language_from_content, subtitle_directory_context};
use super::{MediaKind, Metadata, SubtitleFilename};
use mediakit::inspect::{FileInspector, FilenameInspector, Inspector};
use mediakit::meta::{Tag, fields::MediaType};
use std::path::Path;

impl Metadata {
    /// Inspects a filename and converts its tags into mnamer metadata.
    pub fn inspect(path: &Path, media_override: Option<MediaKind>) -> Self {
        Self::inspect_with_file_content(path, media_override, true)
    }

    /// Inspects media metadata with configurable container probing.
    pub(crate) fn inspect_with_file_content(
        path: &Path,
        media_override: Option<MediaKind>,
        inspect_file_content: bool,
    ) -> Self {
        let filename_inspector = build_filename_inspector(path, media_override);
        let subtitle = SubtitleFilename::from_inspector(&filename_inspector);
        let (mut metadata, mut quality) =
            metadata_from_filename_inspector(filename_inspector, media_override);
        metadata.extension = path
            .extension()
            .and_then(|value| value.to_str())
            .map(|value| value.to_ascii_lowercase());
        let file_inspector = FileInspector::new(path)
            .with_content_inspection(inspect_file_content)
            .analyze();
        for tag in file_inspector.tags() {
            match tag {
                Tag::Container(value) => metadata.container = Some(value.to_ascii_lowercase()),
                Tag::MimeType(value) => metadata.mime_type = Some(value.clone()),
                Tag::FileSize(value) => metadata.file_size = Some(*value),
                _ => merge_file_quality(&mut quality, tag),
            }
        }
        metadata.quality = render_quality(&quality);
        if metadata.container.is_none() {
            metadata.container.clone_from(&metadata.extension);
        }
        if let Some(subtitle) = &subtitle {
            let directory = subtitle_directory_context(path);
            metadata.language_sub = subtitle
                .language
                .or(directory.language)
                .or_else(|| {
                    inspect_file_content
                        .then(|| detect_language_from_content(path, subtitle.format))
                        .flatten()
                })
                .map(|language| language.iso_639_1.to_owned());
            metadata.subtitle_track = subtitle.track.or(directory.track);
            metadata.subtitle_dispositions = directory.dispositions;
            for disposition in &subtitle.dispositions {
                if !metadata.subtitle_dispositions.contains(disposition) {
                    metadata.subtitle_dispositions.push(*disposition);
                }
            }
            if (subtitle.is_generic() || !metadata.has_strong_identity())
                && let Some(ancestor) = strong_ancestor_metadata(path, media_override)
            {
                metadata.overlay(&ancestor);
            }
        }
        metadata
    }
}

/// Inspects metadata encoded in a filename.
fn inspect_filename(path: &Path, media_override: Option<MediaKind>) -> Metadata {
    inspect_filename_parts(path, media_override).0
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
/// Classifies quality metadata for category-aware merging.
enum QualityKind {
    /// Classifies audio codec quality.
    AudioCodec,
    /// Classifies audio channel-layout quality.
    AudioLayout,
    /// Classifies audio codec-profile quality.
    AudioProfile,
    /// Classifies release-source quality.
    ReleaseSource,
    /// Classifies video codec quality.
    VideoCodec,
    /// Classifies video dynamic-range quality.
    VideoDynamicRange,
    /// Classifies video codec-profile quality.
    VideoProfile,
    /// Classifies video resolution quality.
    VideoResolution,
}

#[derive(Debug)]
/// Stores one normalized quality component.
struct QualityPart {
    /// Stores the quality category.
    kind: QualityKind,
    /// Stores the normalized quality value.
    value: String,
}

/// Converts filename tags into metadata and quality components.
fn inspect_filename_parts(
    path: &Path,
    media_override: Option<MediaKind>,
) -> (Metadata, Vec<QualityPart>) {
    metadata_from_filename_inspector(
        build_filename_inspector(path, media_override),
        media_override,
    )
}

/// Builds a filename inspector with an optional media hint.
fn build_filename_inspector(path: &Path, media_override: Option<MediaKind>) -> FilenameInspector {
    let media_hint = media_override.map_or(MediaType::Unknown, |media| match media {
        MediaKind::Movie => MediaType::Movie,
        MediaKind::Episode => MediaType::Television,
        MediaKind::Unknown => MediaType::Unknown,
    });
    FilenameInspector::new(path)
        .with_media_type_hint(media_hint)
        .analyze()
}

/// Converts a completed filename inspection into naming metadata.
fn metadata_from_filename_inspector(
    inspector: FilenameInspector,
    media_override: Option<MediaKind>,
) -> (Metadata, Vec<QualityPart>) {
    let mut metadata = Metadata {
        media_type: media_override.unwrap_or(match inspector.media_type {
            MediaType::Movie => MediaKind::Movie,
            MediaType::Television => MediaKind::Episode,
            MediaType::Unknown => MediaKind::Unknown,
            _ => MediaKind::Unknown,
        }),
        extension: inspector
            .metadata
            .format
            .map(|format| format.extension().to_owned()),
        ..Metadata::default()
    };
    let mut quality = Vec::new();
    let mut alternative_titles = Vec::new();
    for tag in inspector.tags() {
        match tag {
            Tag::Container(value) => metadata.container = Some(value.to_ascii_lowercase()),
            Tag::Title(value) => match metadata.media_type {
                MediaKind::Episode => metadata.series = Some(value.clone()),
                MediaKind::Movie | MediaKind::Unknown => metadata.name = Some(value.clone()),
            },
            Tag::AlternativeTitle(value) => alternative_titles.push(value.clone()),
            Tag::EpisodeTitle(value) => metadata.title = Some(value.clone()),
            Tag::PremiereYear(value) => metadata.year = Some(*value),
            Tag::SeasonNumber(value) => metadata.season = Some(*value),
            Tag::EpisodeNumber(value) => {
                metadata.episode.get_or_insert(*value);
                if !metadata.episodes.contains(value) {
                    metadata.episodes.push(*value);
                }
            }
            Tag::AirDate(value) => metadata.date = Some(value.to_string()),
            Tag::ReleaseGroup(value) => metadata.group = Some(value.to_ascii_uppercase()),
            Tag::AudioLanguage(value) => metadata.language = Some(value.iso_639_1.to_owned()),
            Tag::SubtitleLanguage(value) => {
                metadata.language_sub = Some(value.iso_639_1.to_owned());
            }
            Tag::AudioCodec(_) => quality.push(quality_part(QualityKind::AudioCodec, tag)),
            Tag::AudioLayout(_) => quality.push(quality_part(QualityKind::AudioLayout, tag)),
            Tag::AudioProfile(_) => quality.push(quality_part(QualityKind::AudioProfile, tag)),
            Tag::ReleaseSource(_) => quality.push(quality_part(QualityKind::ReleaseSource, tag)),
            Tag::VideoCodec(_) => quality.push(quality_part(QualityKind::VideoCodec, tag)),
            Tag::VideoDynamicRange(_) => {
                quality.push(quality_part(QualityKind::VideoDynamicRange, tag));
            }
            Tag::VideoProfile(_) => quality.push(quality_part(QualityKind::VideoProfile, tag)),
            Tag::VideoResolution(_) => {
                quality.push(quality_part(QualityKind::VideoResolution, tag));
            }
            _ => {}
        }
    }
    metadata.quality = render_quality(&quality);
    if metadata.container.is_none() {
        metadata.container.clone_from(&metadata.extension);
    }
    if metadata.media_type == MediaKind::Episode && !alternative_titles.is_empty() {
        let alternative = alternative_titles.join(" - ");
        metadata.series = Some(match metadata.series.take() {
            Some(series) if !series.ends_with(&alternative) => format!("{series} - {alternative}"),
            Some(series) => series,
            None => alternative,
        });
    }
    (metadata, quality)
}

/// Converts a metadata tag into one quality component.
fn quality_part(kind: QualityKind, tag: &Tag) -> QualityPart {
    QualityPart {
        kind,
        value: tag.value(),
    }
}

/// Merges probed quality metadata by category.
fn merge_file_quality(quality: &mut Vec<QualityPart>, tag: &Tag) {
    let kind = match tag {
        Tag::AudioCodec(_) => QualityKind::AudioCodec,
        Tag::AudioLayout(_) => QualityKind::AudioLayout,
        Tag::AudioProfile(_) => QualityKind::AudioProfile,
        Tag::VideoCodec(_) => QualityKind::VideoCodec,
        Tag::VideoDynamicRange(_) => QualityKind::VideoDynamicRange,
        Tag::VideoProfile(_) => QualityKind::VideoProfile,
        Tag::VideoResolution(_) => QualityKind::VideoResolution,
        _ => return,
    };
    let value = tag.value();
    if let Some(position) = quality.iter().position(|part| part.kind == kind) {
        quality[position].value = value;
        let mut seen = false;
        quality.retain(|part| {
            if part.kind != kind {
                true
            } else if !seen {
                seen = true;
                true
            } else {
                false
            }
        });
    } else {
        quality.push(QualityPart { kind, value });
    }
}

/// Renders ordered quality components.
fn render_quality(quality: &[QualityPart]) -> Option<String> {
    let mut values = Vec::new();
    for part in quality {
        let value = part.value.to_lowercase();
        if !values.contains(&value) {
            values.push(value);
        }
    }
    (!values.is_empty()).then(|| values.join(" "))
}

/// Finds strong media identity metadata in ancestor directories.
fn strong_ancestor_metadata(path: &Path, media_override: Option<MediaKind>) -> Option<Metadata> {
    let parent = subtitle_directory_context(path)
        .media_directory
        .filter(|parent| parent.file_name().is_some())?;
    let metadata = inspect_filename(parent, media_override);
    metadata.has_strong_identity().then_some(metadata)
}

crate::unit_tests!("inspect.test.rs");
