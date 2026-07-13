//! Defines parsed and provider-enriched naming metadata.

use super::{MediaFormat, MediaKind, SubtitleDisposition};
use serde::{Deserialize, Serialize};

/// Parsed and provider-enriched metadata used for naming a target.
#[derive(Debug, Default, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Metadata {
    /// Detected or explicitly selected media category.
    pub media_type: MediaKind,
    /// Original container without a leading dot.
    pub container: Option<String>,
    /// File-level MIME type inferred from the container.
    pub mime_type: Option<String>,
    /// File size in bytes when the source can be inspected.
    pub file_size: Option<u64>,
    /// File extension without a leading dot.
    pub extension: Option<String>,
    /// Movie title.
    pub name: Option<String>,
    /// Series title.
    pub series: Option<String>,
    /// Episode title.
    pub title: Option<String>,
    /// Premiere year.
    pub year: Option<u16>,
    /// Season number.
    pub season: Option<u16>,
    /// Episode number.
    pub episode: Option<u16>,
    /// All detected episode numbers, including multi-episode releases.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub episodes: Vec<u16>,
    /// Air date in ISO 8601 form.
    pub date: Option<String>,
    /// Release group.
    pub group: Option<String>,
    /// Human-readable quality components.
    pub quality: Option<String>,
    /// Search/audio language identifier.
    pub language: Option<String>,
    /// Subtitle language identifier.
    pub language_sub: Option<String>,
    /// Numeric subtitle track discriminator retained from the source filename.
    pub subtitle_track: Option<u16>,
    /// Subtitle dispositions retained from the source filename.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub subtitle_dispositions: Vec<SubtitleDisposition>,
    /// Provider synopsis.
    pub synopsis: Option<String>,
    /// IMDb identifier.
    pub id_imdb: Option<String>,
    /// TMDb identifier.
    pub id_tmdb: Option<String>,
    /// TVDb identifier.
    pub id_tvdb: Option<String>,
    /// TVmaze identifier.
    pub id_tvmaze: Option<String>,
}

impl Metadata {
    /// Overlays non-empty provider metadata while retaining file-derived fields.
    pub fn overlay(&mut self, other: &Self) {
        macro_rules! overlay {
            ($($field:ident),+ $(,)?) => {
                $(if other.$field.is_some() {
                    self.$field.clone_from(&other.$field);
                })+
            };
        }
        if other.media_type != MediaKind::Unknown {
            self.media_type = other.media_type;
        }
        overlay!(
            name, series, title, year, season, episode, date, synopsis, language, id_imdb, id_tmdb,
            id_tvdb, id_tvmaze
        );
        if !other.episodes.is_empty() {
            self.episodes.clone_from(&other.episodes);
        }
    }

    /// Returns the best human-readable identity for this metadata.
    pub fn display_name(&self) -> &str {
        self.name
            .as_deref()
            .or(self.series.as_deref())
            .or(self.title.as_deref())
            .unwrap_or("Unknown")
    }

    /// Returns whether the underlying file is a supported subtitle.
    pub fn is_subtitle(&self) -> bool {
        self.extension
            .as_deref()
            .and_then(MediaFormat::from_extension)
            .is_some_and(MediaFormat::is_subtitle)
    }

    /// Returns whether the metadata has a strong media identity.
    pub(crate) const fn has_strong_identity(&self) -> bool {
        match self.media_type {
            MediaKind::Movie => self.name.is_some() && self.year.is_some(),
            MediaKind::Episode => {
                self.series.is_some()
                    && (self.date.is_some() || (self.season.is_some() && self.episode.is_some()))
            }
            MediaKind::Unknown => false,
        }
    }
}

crate::unit_tests!("metadata.test.rs");
