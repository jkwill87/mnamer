# AGENTS.md

## Toolchain

Run commands through mise so the pinned Rust 1.97.0 toolchain is used:

- `mise x -- <cmd>` for direct commands
- `mise run <task>` for tasks defined in `mise.toml`

## Commands

| Goal                   | Command                                                    |
| ---------------------- | ---------------------------------------------------------- |
| Build mnamer           | `mise x -- cargo build`                                    |
| Check all targets      | `mise run rust:check`                                      |
| Run deterministic tests| `mise test`                                                |
| Run full test suite    | `mise test --all-features`                                 |
| Run live network tests | `mise run rust:test:net`                                   |
| Lint Rust              | `mise lint`                                                |
| Format Rust            | `mise x -- cargo fmt`                                      |
| Run one test           | `mise x -- cargo test test_name`                           |
| Run the CLI            | `mise x -- cargo run -- help`                              |

## Architecture

- `src/main.rs` is the executable entry point and `src/lib.rs` exposes embeddable application APIs.
- `media` owns inspected metadata plus subtitle filename and directory-chain semantics.
- `net::endpoint` owns HTTP/cache adapters and wire types; `net::provider` owns provider contracts,
  registry, and provider-specific strategies.
- `execute` owns discovery, planning, formatting, preflight, and sequential move/copy/hardlink/
  symlink application.
- `cli::output` owns human/JSON command envelopes.
- `app::ApplicationContext` injects configuration/cache locations and optional candidate sources;
  `app::provider_setup` applies TOML, environment, and embedded credential precedence.
- `mediakit` is an exact-revision Git dependency during initial standalone development.

## Rust conventions and tests

- Keep Rust code formatted with `cargo fmt` and use typed `thiserror` application errors.
- Unit tests are colocated as `*.test.rs` files and included through `#[path = "..."]` modules.
- Integration tests live under `tests/`; live endpoint tests are gated by the `net` feature.
- Prefer `mise test` for deterministic work and `mise run rust:test:net` only when live providers
  are intentionally in scope.
- Do not weaken endpoint expectations to accommodate credential, quota, or upstream-provider drift.
- `--test` is the read-only execution mode for move, copy, hardlink, and symlink.

## Credentials and repository notes

- Runtime API key precedence is `mnamer.toml`, then `API_KEY_TMDB`/`API_KEY_OMDB`/`API_KEY_TVDB`,
  then embedded application fallbacks. TVmaze requires no key.
- Personal local keys belong in gitignored `mise.local.toml`; never print or commit them.
- GitHub Actions injects live-test credentials from repository secrets.
- Generated build output under `target/` is ignored.
