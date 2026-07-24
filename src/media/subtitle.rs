//! Parses subtitle filenames and directory naming conventions.

use mediakit::inspect::{FilenameInspector, Inspector};
use mediakit::meta::Tag;
pub use mediakit::meta::fields::SubtitleDisposition;
use mediakit::meta::fields::{Language, LanguageTag, MediaFormat};
use std::fs::File;
use std::io::Read;
use std::path::Path;

/// Bounds subtitle content read for language detection.
const LANGUAGE_SAMPLE_LIMIT: usize = 64 * 1024;

/// Parsed subtitle sidecar semantics used by inspection, association, and naming.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SubtitleFilename {
    /// Subtitle file format.
    pub format: MediaFormat,
    /// Subtitle language summary; output uses a canonical two-letter code or `multi`.
    pub language: Option<LanguageTag>,
    /// Numeric track discriminator retained from the source name.
    pub track: Option<u16>,
    /// Retained subtitle dispositions in source order.
    pub dispositions: Vec<SubtitleDisposition>,
    /// Stores the normalized media identity stem.
    identity_stem: Option<String>,
    /// Stores the normalized association key.
    association_key: Option<String>,
    /// Indicates whether the subtitle identity is generic.
    generic: bool,
}

impl SubtitleFilename {
    /// Parses subtitle sidecar semantics from the shared filename inspector.
    pub fn parse(path: &Path) -> Option<Self> {
        let inspector = FilenameInspector::new(path).analyze();
        Self::from_inspector(&inspector)
    }

    /// Builds subtitle filename metadata from a completed inspection.
    pub(crate) fn from_inspector(inspector: &FilenameInspector) -> Option<Self> {
        let mut format = None;
        let mut language = None;
        for tag in inspector.tags() {
            match tag {
                Tag::FileFormat(value) if value.is_subtitle() => format = Some(*value),
                Tag::SubtitleLanguage(value) => language = Some(*value),
                _ => {}
            }
        }
        let format = format?;
        let identity_stem = inspector.identity_stem().map(str::to_owned);
        let (track, dispositions) = filename_suffix_metadata(inspector, identity_stem.as_deref());
        let generic = identity_stem.is_none();
        let association_key = (!generic)
            .then(|| identity_stem.as_deref().map(normalize_association_text))
            .flatten()
            .filter(|key| !key.is_empty());
        Some(Self {
            format,
            language,
            track,
            dispositions,
            identity_stem,
            association_key,
            generic,
        })
    }

    /// Returns a punctuation-insensitive key for video/subtitle association.
    pub fn association_key(&self) -> Option<&str> {
        self.association_key.as_deref()
    }

    /// Returns whether the filename carries no useful media identity.
    pub const fn is_generic(&self) -> bool {
        self.generic
    }
}

/// Recovers Mnamer's retained metadata from the subtitle suffix Mediakit identified.
fn filename_suffix_metadata(
    inspector: &FilenameInspector,
    identity_stem: Option<&str>,
) -> (Option<u16>, Vec<SubtitleDisposition>) {
    let Some(stem) = Path::new(inspector.filename())
        .file_stem()
        .and_then(|stem| stem.to_str())
    else {
        return (None, Vec::new());
    };
    let suffix_start = identity_stem
        .and_then(|identity| stem.find(identity).map(|start| start + identity.len()))
        .unwrap_or_default();
    let mut track = None;
    let mut dispositions = Vec::new();
    for token in inspector
        .tokens()
        .iter()
        .filter(|token| token.start >= suffix_start && token.end <= stem.len())
    {
        if let Some(Tag::SubtitleDisposition(disposition)) = token.tag.as_ref() {
            push_unique(&mut dispositions, *disposition);
            continue;
        }
        let Some(value) = inspector.filename().get(token.start..token.end) else {
            continue;
        };
        if is_track_index(value) {
            track = value.parse().ok();
        } else if let Some((marker, number)) = numbered_qualifier(value) {
            track = Some(number);
            if let Marker::Disposition(disposition) = marker {
                push_unique(&mut dispositions, disposition);
            }
        }
    }
    (track, dispositions)
}

/// Appends a disposition once while retaining source order.
fn push_unique(dispositions: &mut Vec<SubtitleDisposition>, disposition: SubtitleDisposition) {
    if !dispositions.contains(&disposition) {
        dispositions.push(disposition);
    }
}

/// Normalizes a media stem so punctuation and whitespace variants compare equally.
pub fn normalize_association_text(value: &str) -> String {
    value
        .chars()
        .flat_map(char::to_lowercase)
        .filter(|character| character.is_alphanumeric())
        .collect()
}

/// Detects subtitle language from bounded text content in supported formats.
pub(crate) fn detect_language_from_content(path: &Path, format: MediaFormat) -> Option<Language> {
    if !matches!(
        format,
        MediaFormat::Srt
            | MediaFormat::Ass
            | MediaFormat::Ssa
            | MediaFormat::Sub
            | MediaFormat::Vtt
    ) {
        return None;
    }

    let mut bytes = Vec::with_capacity(LANGUAGE_SAMPLE_LIMIT + 4);
    File::open(path)
        .ok()?
        .take(u64::try_from(LANGUAGE_SAMPLE_LIMIT + 4).ok()?)
        .read_to_end(&mut bytes)
        .ok()?;
    let text = utf8_sample(&bytes)?;
    let dialogue = dialogue_sample(text, format);
    (!dialogue.trim().is_empty())
        .then(|| Language::detect_from_text(&dialogue))
        .flatten()
}

/// Decodes a bounded UTF-8 sample while tolerating an incomplete trailing character.
fn utf8_sample(bytes: &[u8]) -> Option<&str> {
    let sample = &bytes[..bytes.len().min(LANGUAGE_SAMPLE_LIMIT)];
    let text = match std::str::from_utf8(sample) {
        Ok(text) => text,
        Err(error) if bytes.len() > LANGUAGE_SAMPLE_LIMIT && error.error_len().is_none() => {
            std::str::from_utf8(&sample[..error.valid_up_to()]).ok()?
        }
        Err(_) => return None,
    };
    Some(text.trim_start_matches('\u{feff}'))
}

/// Extracts format-specific dialogue text for language detection.
fn dialogue_sample(text: &str, format: MediaFormat) -> String {
    match format {
        MediaFormat::Ass | MediaFormat::Ssa => text
            .lines()
            .filter_map(|line| {
                let dialogue = line.trim_start().strip_prefix("Dialogue:")?.trim_start();
                dialogue.splitn(10, ',').nth(9).or(Some(dialogue))
            })
            .collect::<Vec<_>>()
            .join("\n"),
        MediaFormat::Sub => text
            .lines()
            .filter_map(microdvd_dialogue)
            .collect::<Vec<_>>()
            .join("\n"),
        MediaFormat::Srt | MediaFormat::Vtt => text
            .lines()
            .map(str::trim)
            .filter(|line| {
                !line.is_empty()
                    && !line.chars().all(|character| character.is_ascii_digit())
                    && !line.contains("-->")
                    && !matches!(*line, "WEBVTT" | "STYLE" | "REGION" | "NOTE")
            })
            .collect::<Vec<_>>()
            .join("\n"),
        _ => String::new(),
    }
}

/// Removes the start and end frame markers from a MicroDVD dialogue line.
fn microdvd_dialogue(line: &str) -> Option<&str> {
    let mut dialogue = line.trim();
    for _ in 0..2 {
        let after_open = dialogue.strip_prefix('{')?;
        let (frame, remainder) = after_open.split_once('}')?;
        if frame.is_empty() || !frame.chars().all(|character| character.is_ascii_digit()) {
            return None;
        }
        dialogue = remainder;
    }
    Some(dialogue)
}

#[derive(Debug, Clone, Copy)]
/// Classifies metadata encoded in subtitle path components.
enum Marker {
    /// Carries a subtitle language marker.
    Language(Language),
    /// Carries a subtitle track-number marker.
    Track(u16),
    /// Carries a subtitle disposition marker.
    Disposition(SubtitleDisposition),
    /// Marks a recognized neutral directory component.
    Neutral,
}

/// Returns whether a directory conventionally contains subtitle sidecars.
pub fn is_subtitle_directory(path: &Path) -> bool {
    path.file_name()
        .and_then(|name| name.to_str())
        .and_then(subtitle_container_markers)
        .is_some()
}

/// Describes subtitle metadata inferred from parent directories.
pub(crate) struct SubtitleDirectoryContext<'a> {
    /// Stores the nearest media directory.
    pub(crate) media_directory: Option<&'a Path>,
    /// Stores the optional subtitle language.
    pub(crate) language: Option<Language>,
    /// Stores the optional subtitle track number.
    pub(crate) track: Option<u16>,
    /// Stores the subtitle dispositions.
    pub(crate) dispositions: Vec<SubtitleDisposition>,
}

/// Resolves subtitle metadata from parent directories.
pub(crate) fn subtitle_directory_context(path: &Path) -> SubtitleDirectoryContext<'_> {
    let immediate = path.parent();
    let mut cursor = immediate;
    let mut groups = Vec::new();

    while let Some(directory) = cursor.filter(|directory| directory.file_name().is_some()) {
        if let Some(container_markers) = directory
            .file_name()
            .and_then(|name| name.to_str())
            .and_then(subtitle_container_markers)
        {
            groups.push(container_markers);
            return resolved_directory_context(directory.parent(), groups);
        }
        let Some(markers) = directory_markers(directory) else {
            break;
        };
        groups.push(markers);
        cursor = directory.parent();
    }

    if !groups.is_empty() {
        return resolved_directory_context(cursor, groups);
    }

    SubtitleDirectoryContext {
        media_directory: immediate,
        language: None,
        track: None,
        dispositions: Vec::new(),
    }
}

/// Builds subtitle directory context from resolved markers.
fn resolved_directory_context(
    media_directory: Option<&Path>,
    groups: Vec<Vec<Marker>>,
) -> SubtitleDirectoryContext<'_> {
    let mut language = None;
    let mut track = None;
    let mut dispositions = Vec::new();
    for marker in groups.into_iter().rev().flatten() {
        match marker {
            Marker::Language(value) => language = Some(value),
            Marker::Track(value) => track = Some(value),
            Marker::Disposition(value) if !dispositions.contains(&value) => {
                dispositions.push(value);
            }
            Marker::Disposition(_) | Marker::Neutral => {}
        }
    }
    SubtitleDirectoryContext {
        media_directory,
        language,
        track,
        dispositions,
    }
}

/// Parses metadata markers from one directory name.
fn directory_markers(path: &Path) -> Option<Vec<Marker>> {
    marker_sequence(path.file_name()?.to_str()?)
}

/// Parses markers from subtitle-container directory names.
fn subtitle_container_markers(value: &str) -> Option<Vec<Marker>> {
    if is_generic_label(value) {
        return Some(Vec::new());
    }
    for (index, separator) in value.char_indices() {
        if separator.is_alphanumeric() {
            continue;
        }
        let tail = &value[index + separator.len_utf8()..];
        if is_generic_label(&value[..index]) {
            return marker_sequence(tail);
        }
        if is_generic_label(tail) {
            return marker_sequence(&value[..index]);
        }
    }
    None
}

/// Parses an ordered metadata-marker sequence.
fn marker_sequence(value: &str) -> Option<Vec<Marker>> {
    if let Some((marker, track)) = numbered_qualifier(value) {
        return Some(vec![marker, Marker::Track(track)]);
    }
    let whole = classify_path_marker(value);
    if let Some(marker @ (Marker::Disposition(_) | Marker::Neutral)) = whole {
        return Some(vec![marker]);
    }
    let split_markers = value
        .split(|character: char| !character.is_alphanumeric())
        .filter(|part| !part.is_empty())
        .map(classify_path_marker)
        .collect::<Option<Vec<_>>>();
    if let Some(markers) = split_markers {
        if markers.len() > 1
            && markers
                .iter()
                .any(|marker| matches!(marker, Marker::Disposition(_) | Marker::Neutral))
        {
            return Some(markers);
        }
        return whole
            .map(|marker| vec![marker])
            .or_else(|| (markers.len() > 1).then_some(markers));
    }
    whole.map(|marker| vec![marker])
}

/// Classifies one path component as a subtitle marker.
fn classify_path_marker(value: &str) -> Option<Marker> {
    classify_marker(trim_marker_wrappers(value)).or_else(|| {
        let value = trim_marker_wrappers(value);
        is_track_index(value).then(|| value.parse().ok().map(Marker::Track))?
    })
}

/// Parses a numbered subtitle qualifier.
fn numbered_qualifier(value: &str) -> Option<(Marker, u16)> {
    let value = trim_marker_wrappers(value);
    let digit_start = value.char_indices().find(|(index, _)| {
        value[*index..]
            .chars()
            .all(|character| character.is_ascii_digit())
    })?;
    let (qualifier, track) = value.split_at(digit_start.0);
    if qualifier.is_empty() || !is_track_index(track) {
        return None;
    }
    let marker = classify_marker(qualifier)?;
    matches!(marker, Marker::Disposition(_) | Marker::Neutral)
        .then(|| track.parse().ok().map(|track| (marker, track)))?
}

/// Removes supported wrappers from a marker.
fn trim_marker_wrappers(value: &str) -> &str {
    value.trim_matches(|character: char| {
        character.is_whitespace() || matches!(character, '(' | ')' | '[' | ']' | '{' | '}')
    })
}

/// Classifies one subtitle marker.
fn classify_marker(value: &str) -> Option<Marker> {
    let normalized = value.trim().to_ascii_lowercase().replace([' ', '_'], "-");
    match normalized.as_str() {
        "forced" => Some(Marker::Disposition(SubtitleDisposition::Forced)),
        "sdh" => Some(Marker::Disposition(SubtitleDisposition::Sdh)),
        "commentary" => Some(Marker::Disposition(SubtitleDisposition::Commentary)),
        "sub" | "subs" | "subtitle" | "subtitles" | "fansub" | "hardsub" | "customsub" | "utf8"
        | "utf-8" | "orig" | "original" | "full" | "hearing-impaired" | "hearingimpaired"
        | "cc" | "closed-caption" | "closed-captions" | "closedcaption" | "default" | "foreign"
        | "sign" | "signs" | "song" | "songs" | "lyrics" => Some(Marker::Neutral),
        _ => Language::from_identifier(&normalized).map(Marker::Language),
    }
}

/// Returns whether a value is a subtitle track index.
fn is_track_index(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 3
        && value.chars().all(|character| character.is_ascii_digit())
}

/// Returns whether a value is a generic subtitle label.
fn is_generic_label(value: &str) -> bool {
    matches!(
        normalize_association_text(value).as_str(),
        "sub" | "subs" | "subtitle" | "subtitles" | "caption" | "captions"
    )
}

crate::unit_tests!("subtitle.test.rs");
