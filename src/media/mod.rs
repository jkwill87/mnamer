//! Classifies and inspects media metadata and subtitle filenames.

mod inspect;
mod kind;
mod metadata;
pub mod subtitle;

pub use kind::MediaKind;
pub use mediakit::meta::fields::MediaFormat;
pub use metadata::Metadata;
pub use subtitle::{SubtitleDisposition, SubtitleFilename};
