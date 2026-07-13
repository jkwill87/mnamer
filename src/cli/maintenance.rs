//! Defines configuration, cache, and provider maintenance commands.

use crate::net::provider::ProviderKind;
use clap::Subcommand;
use std::path::PathBuf;

/// Configuration maintenance operations.
#[derive(Clone, Debug, Subcommand, PartialEq, Eq)]
pub enum ConfigCommand {
    /// Print the selected configuration path or report built-in defaults.
    Path,
    /// Print the effective configuration.
    Show,
    /// Validate an explicit or discovered configuration file.
    Validate {
        /// Explicit file to validate instead of using discovery.
        path: Option<PathBuf>,
    },
    /// Create a documented starter configuration.
    Init {
        /// Destination file, defaulting to the OS-native configuration path.
        path: Option<PathBuf>,
        /// Replace an existing destination file.
        #[arg(long)]
        force: bool,
    },
}

impl ConfigCommand {
    /// Returns the explicit path supplied to validate or init.
    pub const fn path_argument(&self) -> Option<&PathBuf> {
        match self {
            Self::Validate { path } | Self::Init { path, .. } => path.as_ref(),
            Self::Path | Self::Show => None,
        }
    }

    /// Returns whether `config init` may replace an existing file.
    pub const fn force(&self) -> bool {
        matches!(self, Self::Init { force: true, .. })
    }
}

/// Provider-response cache maintenance operations.
#[derive(Clone, Copy, Debug, Subcommand, PartialEq, Eq)]
pub enum CacheCommand {
    /// Print the OS-native provider-response cache path.
    Path,
    /// Remove every provider-response cache entry.
    Clear,
}

/// Metadata-provider inspection operations.
#[derive(Clone, Debug, Subcommand, PartialEq, Eq)]
pub enum ProviderCommand {
    /// List supported providers without making network requests.
    List,
    /// Perform a minimal uncached live request for selected providers.
    Check {
        /// Providers to check; an empty list means every provider.
        #[arg(value_name = "PROVIDER")]
        providers: Vec<ProviderKind>,
    },
}

impl ProviderCommand {
    /// Returns explicitly selected providers, or an empty slice for all providers.
    pub fn providers(&self) -> &[ProviderKind] {
        match self {
            Self::Check { providers } => providers,
            Self::List => &[],
        }
    }
}
