//! Renders safe destination paths from runtime templates.

use crate::media::{MediaKind, Metadata};
use mediakit::meta::fields::Language;
use serde::Serialize;
use std::path::{Component, Path, PathBuf};
use upon::{Engine, Value};

/// Names the internal movie destination template.
const MOVIE_TEMPLATE: &str = "__mnamer_movie";
/// Names the internal episode destination template.
const EPISODE_TEMPLATE: &str = "__mnamer_episode";
/// Prefixes internal movie-directory template names.
const MOVIE_DIRECTORY_TEMPLATE_PREFIX: &str = "__mnamer_movie_directory_";
/// Prefixes internal episode-directory template names.
const EPISODE_DIRECTORY_TEMPLATE_PREFIX: &str = "__mnamer_episode_directory_";

/// Formatting and destination options for movies and episodes.
#[derive(Debug, Clone)]
pub struct FormatOptions {
    /// Movie filename template.
    pub movie_format: String,
    /// Episode filename template.
    pub episode_format: String,
    /// Optional movie destination directory template.
    pub movie_directory: Option<PathBuf>,
    /// Optional episode destination directory template.
    pub episode_directory: Option<PathBuf>,
    /// Convert generated components to lowercase.
    pub lowercase: bool,
    /// Convert generated components to scene-style dotted names.
    pub scene: bool,
}

impl Default for FormatOptions {
    fn default() -> Self {
        Self {
            movie_format: "{{ name }} ({{ year }}).{{ extension }}".into(),
            episode_format:
                "{{ series }} - S{{ season | pad: 2 }}E{{ episode | pad: 2 }} - {{ title }}.{{ extension }}"
                    .into(),
            movie_directory: None,
            episode_directory: None,
            lowercase: false,
            scene: false,
        }
    }
}

/// A template compilation or destination rendering failure.
#[derive(Debug, thiserror::Error)]
pub enum FormatError {
    /// Upon rejected a template or its input.
    #[error("template error: {0}")]
    Template(#[from] upon::Error),
    /// The media type is unknown and no template can be selected.
    #[error("cannot format a target with unknown media type")]
    UnknownMedia,
    /// Rendering produced no filename.
    #[error("template rendered an empty filename")]
    EmptyFilename,
    /// A configured directory template was empty.
    #[error("directory template must not be empty")]
    EmptyDirectory,
}

/// Compiles templates and renders deterministic destinations.
pub struct DestinationFormatter {
    /// Stores the destination template engine.
    engine: Engine<'static>,
    /// Stores the resolved options.
    options: FormatOptions,
}

impl DestinationFormatter {
    /// Creates and validates a destination formatter.
    pub fn new(options: FormatOptions) -> Result<Self, FormatError> {
        if options.movie_format.trim().is_empty() || options.episode_format.trim().is_empty() {
            return Err(FormatError::EmptyFilename);
        }
        if [
            options.movie_directory.as_ref(),
            options.episode_directory.as_ref(),
        ]
        .into_iter()
        .flatten()
        .any(|path| path.as_os_str().is_empty())
        {
            return Err(FormatError::EmptyDirectory);
        }
        let mut engine = Engine::new();
        engine.add_function("first", |value: &str| {
            value
                .chars()
                .next()
                .map_or_else(String::new, |ch| ch.to_string())
        });
        engine.add_function("pad", pad_value);
        engine.add_template(MOVIE_TEMPLATE, options.movie_format.clone())?;
        engine.add_template(EPISODE_TEMPLATE, options.episode_format.clone())?;
        if let Some(path) = &options.movie_directory {
            add_directory_templates(&mut engine, path, MOVIE_DIRECTORY_TEMPLATE_PREFIX)?;
        }
        if let Some(path) = &options.episode_directory {
            add_directory_templates(&mut engine, path, EPISODE_DIRECTORY_TEMPLATE_PREFIX)?;
        }
        let formatter = Self { engine, options };
        formatter.validate_registered_templates()?;
        Ok(formatter)
    }

    /// Renders the final destination for a source and its enriched metadata.
    pub fn destination(&self, source: &Path, metadata: &Metadata) -> Result<PathBuf, FormatError> {
        let mut context = TemplateContext::from(metadata);
        if metadata.is_subtitle()
            && let Some(extension) = metadata.extension.as_deref()
        {
            let mut suffix = metadata
                .language_sub
                .as_deref()
                .and_then(Language::from_identifier)
                .map(|language| vec![language.iso_639_1.to_owned()])
                .unwrap_or_default();
            if let Some(track) = metadata.subtitle_track {
                suffix.push(track.to_string());
            }
            suffix.extend(
                metadata
                    .subtitle_dispositions
                    .iter()
                    .map(|disposition| disposition.suffix().to_owned()),
            );
            suffix.push(extension.trim_start_matches('.').to_ascii_lowercase());
            context.extension = suffix.join(".");
        }
        let template = match metadata.media_type {
            MediaKind::Movie => MOVIE_TEMPLATE,
            MediaKind::Episode => EPISODE_TEMPLATE,
            MediaKind::Unknown => return Err(FormatError::UnknownMedia),
        };
        let rendered = self
            .engine
            .template(template)
            .render(&context)
            .to_string()?;
        let rendered = cleanup_rendered(&rendered);
        if rendered.is_empty() {
            return Err(FormatError::EmptyFilename);
        }
        let rendered_path = Path::new(&rendered);
        let filename = rendered_path
            .file_name()
            .map(|value| self.process_component(&value.to_string_lossy()))
            .filter(|value| !value.is_empty())
            .ok_or(FormatError::EmptyFilename)?;
        let base = match metadata.media_type {
            MediaKind::Movie => self.options.movie_directory.as_deref(),
            MediaKind::Episode => self.options.episode_directory.as_deref(),
            MediaKind::Unknown => None,
        };
        let mut destination = if let Some(base) = base {
            let prefix = match metadata.media_type {
                MediaKind::Movie => MOVIE_DIRECTORY_TEMPLATE_PREFIX,
                MediaKind::Episode => EPISODE_DIRECTORY_TEMPLATE_PREFIX,
                MediaKind::Unknown => unreachable!("unknown media returned above"),
            };
            self.render_directory(base, prefix, &context)?
        } else {
            source
                .parent()
                .unwrap_or_else(|| Path::new("."))
                .to_path_buf()
        };
        for component in rendered_path
            .parent()
            .into_iter()
            .flat_map(Path::components)
        {
            if let Component::Normal(value) = component {
                let value = self.process_component(&value.to_string_lossy());
                if !value.is_empty() {
                    destination.push(value);
                }
            }
        }
        destination.push(filename);
        Ok(std::path::absolute(&destination).unwrap_or(destination))
    }

    /// Renders one configured destination directory component.
    fn render_directory(
        &self,
        template: &Path,
        template_name_prefix: &str,
        context: &TemplateContext,
    ) -> Result<PathBuf, FormatError> {
        let absolute = template.is_absolute();
        let mut output = PathBuf::new();
        for (index, component) in template.components().enumerate() {
            match component {
                Component::Prefix(value) => output.push(value.as_os_str()),
                Component::RootDir => output.push(component.as_os_str()),
                Component::CurDir => output.push("."),
                Component::ParentDir => output.push(".."),
                Component::Normal(value) => {
                    let original = value.to_string_lossy();
                    let generated = ["{{", "{%", "{#"]
                        .iter()
                        .any(|marker| original.contains(marker));
                    if absolute && !generated {
                        output.push(value);
                        continue;
                    }
                    let rendered = self
                        .engine
                        .template(&directory_template_name(template_name_prefix, index))
                        .render(context)
                        .to_string()?;
                    let rendered = cleanup_rendered(&rendered);
                    output.push(self.process_component(&rendered));
                }
            }
        }
        Ok(output)
    }

    /// Sanitizes one rendered path component.
    fn process_component(&self, value: &str) -> String {
        let mut output = String::with_capacity(value.len());
        let mut previous_space = false;
        for ch in value.chars() {
            if ch.is_control() || matches!(ch, '<' | '>' | ':' | '"' | '|' | '?' | '*' | '/' | '\\')
            {
                continue;
            }
            if ch.is_whitespace() {
                if !previous_space {
                    output.push(' ');
                }
                previous_space = true;
            } else {
                output.push(ch);
                previous_space = false;
            }
        }
        let mut output = output.trim_matches([' ', '-', '.', ',']).to_owned();
        if self.options.scene {
            output = scene_component(&output);
        } else if self.options.lowercase {
            output = output.to_lowercase();
        }
        protect_reserved_filename(&mut output);
        output
    }

    /// Validates all registered destination templates.
    fn validate_registered_templates(&self) -> Result<(), upon::Error> {
        let context = TemplateContext::from(&Metadata {
            media_type: MediaKind::Episode,
            container: Some("mkv".into()),
            mime_type: Some("video/x-matroska".into()),
            file_size: Some(1),
            extension: Some("mkv".into()),
            name: Some("Clerks III".into()),
            series: Some("Silicon Valley".into()),
            title: Some("Minimum Viable Product".into()),
            year: Some(2024),
            season: Some(1),
            episode: Some(2),
            episodes: vec![2, 3],
            date: Some("2024-01-02".into()),
            group: Some("FLAME".into()),
            quality: Some("1080p".into()),
            language: Some("en".into()),
            language_sub: Some("en".into()),
            subtitle_track: None,
            subtitle_dispositions: Vec::new(),
            synopsis: Some("Example synopsis".into()),
            id_imdb: Some("tt1".into()),
            id_tmdb: Some("1".into()),
            id_tvdb: Some("2".into()),
            id_tvmaze: Some("3".into()),
        });
        for name in [MOVIE_TEMPLATE, EPISODE_TEMPLATE] {
            self.engine.template(name).render(&context).to_string()?;
        }
        for (path, prefix) in [
            (
                self.options.movie_directory.as_deref(),
                MOVIE_DIRECTORY_TEMPLATE_PREFIX,
            ),
            (
                self.options.episode_directory.as_deref(),
                EPISODE_DIRECTORY_TEMPLATE_PREFIX,
            ),
        ] {
            let Some(path) = path else { continue };
            for (index, component) in path.components().enumerate() {
                if matches!(component, Component::Normal(_)) {
                    self.engine
                        .template(&directory_template_name(prefix, index))
                        .render(&context)
                        .to_string()?;
                }
            }
        }
        Ok(())
    }
}

#[derive(Debug, Serialize)]
/// Supplies metadata values to destination templates.
struct TemplateContext {
    /// Stores the media container.
    container: String,
    /// Stores the media MIME type.
    mime_type: String,
    /// Stores the optional file size.
    file_size: Option<u64>,
    /// Stores the file extension.
    extension: String,
    /// Stores the movie name.
    name: String,
    /// Stores the series name.
    series: String,
    /// Stores the episode title.
    title: String,
    /// Stores the optional premiere year.
    year: Option<u16>,
    /// Stores the optional season number.
    season: Option<u16>,
    /// Stores the optional episode number.
    episode: Option<u16>,
    /// Stores the episode numbers.
    episodes: Vec<u16>,
    /// Stores the air date.
    date: String,
    /// Stores the release group.
    group: String,
    /// Stores the quality description.
    quality: String,
    /// Stores the language.
    language: String,
    /// Stores the subtitle language.
    language_sub: String,
    /// Stores the optional subtitle track number.
    subtitle_track: Option<u16>,
    /// Stores the subtitle dispositions.
    subtitle_dispositions: Vec<String>,
    /// Stores the media synopsis.
    synopsis: String,
    /// Stores the IMDb identifier.
    id_imdb: String,
    /// Stores the TMDb identifier.
    id_tmdb: String,
    /// Stores the TVDb identifier.
    id_tvdb: String,
    /// Stores the TVmaze identifier.
    id_tvmaze: String,
}

impl From<&Metadata> for TemplateContext {
    fn from(value: &Metadata) -> Self {
        Self {
            container: template_text(value.container.as_deref(), false),
            mime_type: template_text(value.mime_type.as_deref(), false),
            file_size: value.file_size,
            extension: template_text(value.extension.as_deref(), false)
                .trim_start_matches('.')
                .to_owned(),
            name: template_text(value.name.as_deref(), true),
            series: template_text(value.series.as_deref(), true),
            title: template_text(value.title.as_deref(), true),
            year: value.year,
            season: value.season,
            episode: value.episode,
            episodes: value.episodes.clone(),
            date: template_text(value.date.as_deref(), false),
            group: template_text(value.group.as_deref(), false),
            quality: template_text(value.quality.as_deref(), false),
            language: template_text(value.language.as_deref(), false),
            language_sub: template_text(value.language_sub.as_deref(), false),
            subtitle_track: value.subtitle_track,
            subtitle_dispositions: value
                .subtitle_dispositions
                .iter()
                .map(|disposition| disposition.suffix().to_owned())
                .collect(),
            synopsis: template_text(value.synopsis.as_deref(), true),
            id_imdb: template_text(value.id_imdb.as_deref(), false),
            id_tmdb: template_text(value.id_tmdb.as_deref(), false),
            id_tvdb: template_text(value.id_tvdb.as_deref(), false),
            id_tvmaze: template_text(value.id_tvmaze.as_deref(), false),
        }
    }
}

/// Pads a template value to a requested width.
fn pad_value(value: &Value, width: i64) -> String {
    let width = usize::try_from(width.clamp(0, 32)).unwrap_or_default();
    match value {
        Value::Integer(value) => format!("{value:0width$}"),
        Value::String(value) if !value.is_empty() => format!("{value:0>width$}"),
        Value::None | Value::String(_) => String::new(),
        Value::Float(value) if value.fract() == 0.0 => {
            format!("{:0width$}", *value as i64)
        }
        Value::Bool(_) | Value::Float(_) | Value::List(_) | Value::Map(_) => String::new(),
    }
}

/// Registers configured directory templates.
fn add_directory_templates(
    engine: &mut Engine<'static>,
    path: &Path,
    template_name_prefix: &str,
) -> Result<(), upon::Error> {
    for (index, component) in path.components().enumerate() {
        if let Component::Normal(value) = component {
            engine.add_template(
                directory_template_name(template_name_prefix, index),
                value.to_string_lossy().into_owned(),
            )?;
        }
    }
    Ok(())
}

/// Builds the internal name for a directory template.
fn directory_template_name(prefix: &str, index: usize) -> String {
    format!("{prefix}{index}")
}

/// Cleans delimiters and whitespace from rendered output.
fn cleanup_rendered(value: &str) -> String {
    let mut value = remove_empty_delimiters(value);
    value = collapse_whitespace(&value);
    for (from, to) in [
        (" - - ", " - "),
        (" -- ", " - "),
        (" - .", "."),
        (" -.", "."),
        (" , .", "."),
        (", .", "."),
        (" .", "."),
    ] {
        while value.contains(from) {
            value = value.replace(from, to);
        }
    }
    value.trim_matches([' ', '-', '.', ',']).to_owned()
}

/// Removes delimiters left around empty template fields.
fn remove_empty_delimiters(value: &str) -> String {
    let chars = value.chars().collect::<Vec<_>>();
    let mut output = String::with_capacity(value.len());
    let mut index = 0;
    while index < chars.len() {
        let closing = match chars[index] {
            '(' => Some(')'),
            '[' => Some(']'),
            '{' => Some('}'),
            _ => None,
        };
        if let Some(closing) = closing {
            let mut next = index + 1;
            while next < chars.len() && chars[next].is_whitespace() {
                next += 1;
            }
            if chars.get(next) == Some(&closing) {
                index = next + 1;
                continue;
            }
        }
        output.push(chars[index]);
        index += 1;
    }
    output
}

/// Collapses consecutive whitespace.
fn collapse_whitespace(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut in_whitespace = false;
    for ch in value.chars() {
        if ch.is_whitespace() {
            if !in_whitespace {
                output.push(' ');
            }
            in_whitespace = true;
        } else {
            output.push(ch);
            in_whitespace = false;
        }
    }
    output
}

/// Transforms a value into a scene-style path component.
fn scene_component(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    let mut previous_dot = false;
    for ch in value.chars().flat_map(char::to_lowercase) {
        if ch.is_alphanumeric() {
            output.push(ch);
            previous_dot = false;
        } else if !previous_dot {
            output.push('.');
            previous_dot = true;
        }
    }
    output.trim_matches('.').to_owned()
}

/// Converts optional metadata into template text.
fn template_text(value: Option<&str>, title: bool) -> String {
    let value = value.unwrap_or_default().replace(['/', '\\'], " - ");
    let value = collapse_whitespace(&value);
    if title { title_case(&value) } else { value }
}

/// Applies media-aware title casing.
fn title_case(value: &str) -> String {
    const LOWERCASE_WORDS: &[&str] = &[
        "a", "an", "and", "as", "at", "but", "by", "de", "des", "du", "en", "for", "from", "if",
        "in", "is", "le", "nor", "of", "on", "or", "per", "the", "to", "un", "une", "via", "vs",
        "with",
    ];
    const UPPERCASE_WORDS: &[&str] = &[
        "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv",
        "xv", "xvi", "xvii", "xviii", "xix", "xx", "2d", "3d", "a24", "abc", "ac", "ai", "aids",
        "aka", "amc", "atm", "au", "bbc", "bff", "cbs", "cia", "cnn", "csi", "dc", "diy", "dna",
        "doa", "dvd", "espn", "eu", "fbi", "gps", "hbo", "hd", "hiv", "imax", "ira", "irs", "jfk",
        "lgbt", "lgbtq", "lol", "mcu", "mlb", "mlk", "mls", "mtv", "nasa", "nba", "nbc", "ncaa",
        "nfl", "nhl", "nsa", "nsfw", "nyc", "nypd", "oj", "ok", "omg", "pbs", "pga", "rsvp", "sos",
        "swat", "tbs", "tnt", "tv", "ufc", "ufo", "uhd", "uk", "usa", "vhs", "vip", "vr", "wnba",
        "wtf", "wwe", "wwi", "wwii", "xxx", "yolo",
    ];

    let word_count = value
        .split(|ch: char| !ch.is_alphanumeric() && ch != '\'' && ch != '’')
        .filter(|word| !word.is_empty())
        .count();
    let mut word_index = 0;
    let mut output = String::with_capacity(value.len());
    let mut token = String::new();
    for ch in value.chars().chain(std::iter::once('\0')) {
        if ch.is_alphanumeric() || matches!(ch, '\'' | '’') {
            token.push(ch);
            continue;
        }
        if !token.is_empty() {
            let lowercase = token.to_lowercase();
            let transformed = if UPPERCASE_WORDS.contains(&lowercase.as_str()) {
                lowercase.to_uppercase()
            } else if word_index > 0
                && word_index + 1 < word_count
                && LOWERCASE_WORDS.contains(&lowercase.as_str())
            {
                lowercase
            } else {
                uppercase_initial(&lowercase)
            };
            output.push_str(&transformed);
            token.clear();
            word_index += 1;
        }
        if ch != '\0' {
            output.push(ch);
        }
    }
    output
}

/// Uppercases the first character of a value.
fn uppercase_initial(value: &str) -> String {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return String::new();
    };
    first.to_uppercase().chain(chars).collect()
}

/// Protects reserved Windows filenames.
fn protect_reserved_filename(value: &mut String) {
    let stem = value.split('.').next().unwrap_or_default();
    let uppercase = stem.to_ascii_uppercase();
    let numbered_device = uppercase
        .strip_prefix("COM")
        .or_else(|| uppercase.strip_prefix("LPT"))
        .is_some_and(|number| {
            matches!(number, "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9")
        });
    if matches!(uppercase.as_str(), "CON" | "PRN" | "AUX" | "NUL") || numbered_device {
        value.insert(0, '_');
    }
}

crate::unit_tests!("format.test.rs");
