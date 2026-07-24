#!/usr/bin/env bash

set -euo pipefail

manifest="${1:-Cargo.toml}"

: "${GITHUB_REF_TYPE:?GITHUB_REF_TYPE is required}"
: "${GITHUB_REF_NAME:?GITHUB_REF_NAME is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"

if [[ "$GITHUB_REF_TYPE" == "tag" ]]; then
  if [[ ! "$GITHUB_REF_NAME" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo "Release tags must use the vMAJOR.MINOR.PATCH format." >&2
    exit 1
  fi

  version="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
  channel="release"
elif [[ "$GITHUB_REF_TYPE" == "branch" && "$GITHUB_REF_NAME" == "v3" ]]; then
  : "${GITHUB_RUN_NUMBER:?GITHUB_RUN_NUMBER is required for development releases}"

  git rev-parse --git-dir >/dev/null

  if [[ ! "$GITHUB_RUN_NUMBER" =~ ^[0-9]+$ ]]; then
    echo "The GitHub run number must be numeric." >&2
    exit 1
  fi

  latest_tag=""
  while IFS= read -r tag; do
    if [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      latest_tag="$tag"
      break
    fi
  done < <(git tag --merged HEAD --sort=-version:refname)

  if [[ -n "$latest_tag" ]]; then
    base_version="${latest_tag#v}"
  else
    base_version="$(awk -F '"' '/^version = "[^"]+"$/ { print $2; exit }' "$manifest")"
  fi

  if [[ ! "$base_version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo "The development release base must be a stable semantic version." >&2
    exit 1
  fi

  version="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3] + 1))-dev${GITHUB_RUN_NUMBER}"
  channel="development"
else
  echo "Packages can only be published from v3 or a vMAJOR.MINOR.PATCH tag." >&2
  exit 1
fi

printf 'version=%s\n' "$version" >> "$GITHUB_OUTPUT"
printf 'channel=%s\n' "$channel" >> "$GITHUB_OUTPUT"
printf 'Publishing mnamer %s (%s)\n' "$version" "$channel"
