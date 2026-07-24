#!/usr/bin/env bash

set -euo pipefail

v3_first_commit="${MNAMER_V3_FIRST_COMMIT:-53262623add8d050c889305e4ff5b114ae0528fd}"

: "${GITHUB_REF_TYPE:?GITHUB_REF_TYPE is required}"
: "${GITHUB_REF_NAME:?GITHUB_REF_NAME is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"

publish="true"

if [[ "$GITHUB_REF_TYPE" == "tag" ]]; then
  if [[ ! "$GITHUB_REF_NAME" =~ ^v([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
    echo "Release tags must use the vMAJOR.MINOR.PATCH format." >&2
    exit 1
  fi

  version="${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.${BASH_REMATCH[3]}"
  channel="release"
elif [[ "$GITHUB_REF_TYPE" == "branch" && "$GITHUB_REF_NAME" == "v3" ]]; then
  git rev-parse --git-dir >/dev/null

  if ! git cat-file -e "${v3_first_commit}^{commit}" 2>/dev/null; then
    echo "The first v3 commit does not exist: ${v3_first_commit}" >&2
    exit 1
  fi

  if ! git merge-base --is-ancestor "$v3_first_commit" HEAD; then
    echo "The first v3 commit is not an ancestor of HEAD: ${v3_first_commit}" >&2
    exit 1
  fi

  commit_count="$((
    $(git rev-list --first-parent --count "${v3_first_commit}..HEAD") + 1
  ))"
  if [[ ! "$commit_count" =~ ^[1-9][0-9]*$ ]]; then
    echo "The v3 development commit count must be positive." >&2
    exit 1
  fi

  version="3.0.0-dev${commit_count}"
  channel="development"
elif [[ "$GITHUB_REF_TYPE" == "branch" && "$GITHUB_REF_NAME" == "main" ]]; then
  git rev-parse --git-dir >/dev/null

  latest_tag=""
  while IFS= read -r tag; do
    if [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      latest_tag="$tag"
      break
    fi
  done < <(git tag --merged HEAD --sort=-version:refname)

  if [[ -z "$latest_tag" ]]; then
    publish="false"
    channel="development"
    echo "Skipping a main development release until a stable vMAJOR.MINOR.PATCH tag is reachable."
  else
    base_version="${latest_tag#v}"
    if [[ ! "$base_version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
      echo "The latest stable tag has an invalid version: ${latest_tag}" >&2
      exit 1
    fi

    major="${BASH_REMATCH[1]}"
    minor="${BASH_REMATCH[2]}"
    patch="${BASH_REMATCH[3]}"
    commit_count="$(git rev-list --first-parent --count "${latest_tag}..HEAD")"

    if [[ "$commit_count" == "0" ]]; then
      publish="false"
      channel="development"
      echo "Skipping a main development release at stable tag ${latest_tag}."
    elif [[ "$commit_count" =~ ^[1-9][0-9]*$ ]]; then
      version="${major}.${minor}.$((patch + 1))-dev${commit_count}"
      channel="development"
    else
      echo "The main development commit count must be non-negative." >&2
      exit 1
    fi
  fi
else
  echo "Packages can only be published from v3, main, or a vMAJOR.MINOR.PATCH tag." >&2
  exit 1
fi

printf 'channel=%s\n' "$channel" >> "$GITHUB_OUTPUT"
printf 'publish=%s\n' "$publish" >> "$GITHUB_OUTPUT"

if [[ "$publish" == "true" ]]; then
  printf 'version=%s\n' "$version" >> "$GITHUB_OUTPUT"
  printf 'Publishing mnamer %s (%s)\n' "$version" "$channel"
fi
