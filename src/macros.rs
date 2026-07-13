//! Defines the colocated unit-test module macro.

/// Includes a colocated unit-test module only when compiling tests.
macro_rules! unit_tests {
    ($path:literal) => {
        #[cfg(test)]
        #[path = $path]
        mod tests;
    };
}
pub(crate) use unit_tests;
