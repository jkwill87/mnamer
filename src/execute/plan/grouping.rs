//! Groups video files with associated subtitle sidecars.

use crate::media::subtitle::{normalize_association_text, subtitle_directory_context};
use crate::media::{MediaKind, Metadata, SubtitleFilename};
use std::path::{Path, PathBuf};
use unicode_normalization::{UnicodeNormalization, char::is_combining_mark};

#[derive(Debug)]
/// Stores one inspected discovery item with its source order.
pub(super) struct ParsedItem {
    /// Stores the discovery-order index.
    pub(super) index: usize,
    /// Stores the source path.
    pub(super) source: PathBuf,
    /// Stores the inspected metadata.
    pub(super) metadata: Metadata,
}

#[derive(Debug, Clone)]
/// Groups one primary media item with associated sidecars.
pub(super) struct LogicalTarget {
    /// Stores the logical-target order.
    pub(super) order: usize,
    /// Stores the primary item index.
    pub(super) primary: usize,
    /// Stores the associated item indexes.
    pub(super) members: Vec<usize>,
}

/// Groups subtitle sidecars with their matching video targets.
pub(super) fn group_subtitles(parsed: &[ParsedItem]) -> Vec<LogicalTarget> {
    let video_indexes = parsed
        .iter()
        .enumerate()
        .filter_map(|(index, item)| (!item.metadata.is_subtitle()).then_some(index))
        .collect::<Vec<_>>();
    let mut groups = video_indexes
        .iter()
        .map(|&index| LogicalTarget {
            order: parsed[index].index,
            primary: index,
            members: vec![index],
        })
        .collect::<Vec<_>>();

    for (subtitle_index, subtitle) in parsed
        .iter()
        .enumerate()
        .filter(|(_, item)| item.metadata.is_subtitle())
    {
        let descriptor = SubtitleFilename::parse(&subtitle.source);
        let eligible = groups
            .iter()
            .enumerate()
            .filter(|(_, group)| {
                let video = &parsed[group.primary].source;
                !parsed[group.primary].metadata.is_subtitle()
                    && video.parent()
                        == subtitle_directory_context(&subtitle.source).media_directory
            })
            .collect::<Vec<_>>();
        let stem_matches = descriptor
            .as_ref()
            .and_then(SubtitleFilename::association_key)
            .map(|subtitle_key| {
                eligible
                    .iter()
                    .filter_map(|(position, group)| {
                        video_association_key(&parsed[group.primary].source)
                            .is_some_and(|video_key| video_key == subtitle_key)
                            .then_some(*position)
                    })
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();
        let semantic_matches = eligible
            .iter()
            .filter_map(|(position, group)| {
                same_media_identity(&subtitle.metadata, &parsed[group.primary].metadata)
                    .then_some(*position)
            })
            .collect::<Vec<_>>();
        let fuzzy_matches = eligible
            .iter()
            .filter_map(|(position, group)| {
                sole_fallback_compatible(&subtitle.metadata, &parsed[group.primary].metadata)
                    .then_some(*position)
            })
            .collect::<Vec<_>>();
        let sole_eligible = match eligible.as_slice() {
            [(position, group)]
                if sole_fallback_compatible(
                    &subtitle.metadata,
                    &parsed[group.primary].metadata,
                ) =>
            {
                Some(*position)
            }
            [] | [_, _, ..] => None,
            [(_, _)] => None,
        };
        let matching_group = unique_position(&stem_matches)
            .or_else(|| unique_position(&semantic_matches))
            .or_else(|| unique_position(&fuzzy_matches))
            .or(sole_eligible);

        if let Some(position) = matching_group {
            groups[position].members.push(subtitle_index);
            groups[position].order = groups[position].order.min(subtitle.index);
        } else if let Some(position) = groups.iter().position(|group| {
            parsed[group.primary].metadata.is_subtitle()
                && subtitle_companions(&parsed[group.primary], subtitle)
        }) {
            groups[position].members.push(subtitle_index);
            groups[position].order = groups[position].order.min(subtitle.index);
        } else {
            groups.push(LogicalTarget {
                order: subtitle.index,
                primary: subtitle_index,
                members: vec![subtitle_index],
            });
        }
    }
    groups.sort_by_key(|group| group.order);
    groups
}

/// Builds a normalized video-association key from a path.
fn video_association_key(path: &Path) -> Option<String> {
    path.file_stem()
        .and_then(|value| value.to_str())
        .map(normalize_association_text)
        .filter(|key| !key.is_empty())
}

/// Returns whether two metadata values share a media identity.
fn same_media_identity(left: &Metadata, right: &Metadata) -> bool {
    match (left.media_type, right.media_type) {
        (MediaKind::Movie, MediaKind::Movie) => {
            compatible_value(left.year, right.year)
                && normalized_metadata_name(left.name.as_deref()).is_some()
                && normalized_metadata_name(left.name.as_deref())
                    == normalized_metadata_name(right.name.as_deref())
        }
        (MediaKind::Episode, MediaKind::Episode) => {
            normalized_metadata_name(left.series.as_deref())
                == normalized_metadata_name(right.series.as_deref())
                && compatible_value(left.season, right.season)
                && compatible_value(left.episode, right.episode)
                && compatible_ref(left.date.as_deref(), right.date.as_deref())
                && (left.season.is_some()
                    || left.episode.is_some()
                    || left.date.is_some()
                    || right.season.is_some()
                    || right.episode.is_some()
                    || right.date.is_some())
        }
        (MediaKind::Unknown, _)
        | (_, MediaKind::Unknown)
        | (MediaKind::Movie, MediaKind::Episode)
        | (MediaKind::Episode, MediaKind::Movie) => false,
    }
}

/// Returns whether two optional owned values are compatible.
fn compatible_value<T: PartialEq>(left: Option<T>, right: Option<T>) -> bool {
    left.is_none() || right.is_none() || left == right
}

/// Returns whether two optional borrowed values are compatible.
fn compatible_ref<T: PartialEq + ?Sized>(left: Option<&T>, right: Option<&T>) -> bool {
    left.is_none() || right.is_none() || left == right
}

/// Normalizes a metadata name for matching.
fn normalized_metadata_name(value: Option<&str>) -> Option<String> {
    value
        .map(normalize_association_text)
        .filter(|value| !value.is_empty())
}

/// Returns whether two items qualify for sole-video fallback.
fn sole_fallback_compatible(left: &Metadata, right: &Metadata) -> bool {
    match (left.media_type, right.media_type) {
        (MediaKind::Movie, MediaKind::Movie) => {
            !conflicting_value(left.year, right.year)
                && fuzzy_name_compatible(left.name.as_deref(), right.name.as_deref())
        }
        (MediaKind::Episode, MediaKind::Episode) => {
            !conflicting_value(left.season, right.season)
                && !conflicting_value(left.episode, right.episode)
                && !conflicting_ref(left.date.as_deref(), right.date.as_deref())
                && fuzzy_name_compatible(left.series.as_deref(), right.series.as_deref())
        }
        (MediaKind::Unknown, _) | (_, MediaKind::Unknown) => true,
        (MediaKind::Movie, MediaKind::Episode) | (MediaKind::Episode, MediaKind::Movie) => false,
    }
}

/// Returns whether two optional owned values conflict.
fn conflicting_value<T: PartialEq>(left: Option<T>, right: Option<T>) -> bool {
    left.is_some() && right.is_some() && left != right
}

/// Returns whether two optional borrowed values conflict.
fn conflicting_ref<T: PartialEq + ?Sized>(left: Option<&T>, right: Option<&T>) -> bool {
    left.is_some() && right.is_some() && left != right
}

/// Returns whether two names are fuzzily compatible.
fn fuzzy_name_compatible(left: Option<&str>, right: Option<&str>) -> bool {
    let (Some(left), Some(right)) = (left, right) else {
        return true;
    };
    let left = folded_metadata_tokens(left);
    let right = folded_metadata_tokens(right);
    if left.is_empty() || right.is_empty() {
        return true;
    }
    left == right
        || contains_token_sequence(&left, &right)
        || contains_token_sequence(&right, &left)
}

/// Returns whether one token sequence contains another.
fn contains_token_sequence(haystack: &[String], needle: &[String]) -> bool {
    !needle.is_empty()
        && needle.iter().map(String::len).sum::<usize>() >= 3
        && haystack
            .windows(needle.len())
            .any(|window| window == needle)
}

/// Tokenizes and folds metadata text for fuzzy matching.
fn folded_metadata_tokens(value: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut token = String::new();
    for character in value
        .nfkd()
        .flat_map(char::to_lowercase)
        .filter(|character| !is_combining_mark(*character))
    {
        match character {
            'à' | 'á' | 'â' | 'ã' | 'ä' | 'å' | 'ā' => token.push('a'),
            'ç' | 'ć' | 'č' => token.push('c'),
            'ď' | 'đ' | 'ð' => token.push('d'),
            'è' | 'é' | 'ê' | 'ë' | 'ē' => token.push('e'),
            'ì' | 'í' | 'î' | 'ï' | 'ī' => token.push('i'),
            'ı' => token.push('i'),
            'ł' => token.push('l'),
            'ñ' | 'ń' => token.push('n'),
            'ò' | 'ó' | 'ô' | 'õ' | 'ö' | 'ø' | 'ō' => token.push('o'),
            'ř' => token.push('r'),
            'ś' | 'š' => token.push('s'),
            'ť' => token.push('t'),
            'ù' | 'ú' | 'û' | 'ü' | 'ū' => token.push('u'),
            'ý' | 'ÿ' => token.push('y'),
            'ž' | 'ź' | 'ż' => token.push('z'),
            'æ' => token.push_str("ae"),
            'œ' => token.push_str("oe"),
            'ß' => token.push_str("ss"),
            'þ' => token.push_str("th"),
            character if character.is_alphanumeric() => token.push(character),
            character
                if (character.is_whitespace() || character.is_ascii_punctuation())
                    && !token.is_empty() =>
            {
                tokens.push(std::mem::take(&mut token));
            }
            _ => {}
        }
    }
    if !token.is_empty() {
        tokens.push(token);
    }
    tokens
}

/// Returns whether two subtitle files form a companion pair.
fn subtitle_companions(left: &ParsedItem, right: &ParsedItem) -> bool {
    if left.source.parent() != right.source.parent() {
        return false;
    }
    let (Some(left_name), Some(right_name)) = (
        SubtitleFilename::parse(&left.source),
        SubtitleFilename::parse(&right.source),
    ) else {
        return false;
    };
    if left_name.format == right_name.format
        || left_name.language != right_name.language
        || left_name.track != right_name.track
        || left_name.dispositions != right_name.dispositions
    {
        return false;
    }
    match (left_name.association_key(), right_name.association_key()) {
        (Some(left), Some(right)) => left == right,
        (None, None) if left_name.is_generic() && right_name.is_generic() => true,
        (Some(_), None) | (None, Some(_)) | (None, None) => {
            same_media_identity(&left.metadata, &right.metadata)
        }
    }
}

/// Returns the sole position when exactly one exists.
fn unique_position(positions: &[usize]) -> Option<usize> {
    match positions {
        [position] => Some(*position),
        [] | [_, _, ..] => None,
    }
}
