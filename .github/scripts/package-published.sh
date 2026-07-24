#!/usr/bin/env bash

set -euo pipefail

version="${1:?A package version is required}"
status="${MNAMER_REGISTRY_STATUS:-}"

if [[ -z "$status" ]]; then
  status="$(curl --retry 3 --silent --show-error --output /dev/null --write-out '%{http_code}' \
    --user-agent 'mnamer-release-workflow (https://github.com/jkwill87/mnamer)' \
    "https://crates.io/api/v1/crates/mnamer/$version")"
fi

case "$status" in
  200)
    echo "published=true" >> "$GITHUB_OUTPUT"
    echo "mnamer $version is already published; skipping this rerun."
    ;;
  404)
    echo "published=false" >> "$GITHUB_OUTPUT"
    ;;
  *)
    echo "crates.io returned HTTP $status while checking mnamer $version." >&2
    exit 1
    ;;
esac
