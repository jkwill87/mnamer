#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
version_script="$script_dir/package-version.sh"
published_script="$script_dir/package-published.sh"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

new_repository() {
  local repository="$1"
  git init --quiet --initial-branch=main "$repository"
  git -C "$repository" config user.email "release-tests@example.com"
  git -C "$repository" config user.name "Release Tests"
}

commit() {
  local repository="$1"
  local message="$2"
  git -C "$repository" commit --quiet --allow-empty --message "$message"
}

run_version() {
  local repository="$1"
  local ref_type="$2"
  local ref_name="$3"
  local output="$4"
  shift 4

  (
    cd "$repository"
    env \
      GITHUB_REF_TYPE="$ref_type" \
      GITHUB_REF_NAME="$ref_name" \
      GITHUB_OUTPUT="$output" \
      "$@" \
      bash "$version_script"
  )
}

assert_output() {
  local output="$1"
  local expected="$2"
  if ! grep --fixed-strings --line-regexp --quiet "$expected" "$output"; then
    echo "Expected '$expected' in $output:" >&2
    sed 's/^/  /' "$output" >&2
    exit 1
  fi
}

assert_no_version() {
  local output="$1"
  if grep --quiet '^version=' "$output"; then
    echo "Did not expect a version in $output:" >&2
    sed 's/^/  /' "$output" >&2
    exit 1
  fi
}

v3_repository="$test_root/v3"
new_repository "$v3_repository"
commit "$v3_repository" "first v3 commit"
v3_first_commit="$(git -C "$v3_repository" rev-parse HEAD)"

output="$test_root/v3-first.output"
run_version "$v3_repository" branch v3 "$output" MNAMER_V3_FIRST_COMMIT="$v3_first_commit"
assert_output "$output" "version=3.0.0-dev1"
assert_output "$output" "publish=true"

commit "$v3_repository" "second v3 commit"
git -C "$v3_repository" switch --quiet --create topic
commit "$v3_repository" "topic commit one"
commit "$v3_repository" "topic commit two"
git -C "$v3_repository" switch --quiet main
git -C "$v3_repository" merge --quiet --no-ff topic --message "merge topic"

output="$test_root/v3-merge.output"
run_version "$v3_repository" branch v3 "$output" MNAMER_V3_FIRST_COMMIT="$v3_first_commit"
assert_output "$output" "version=3.0.0-dev3"

unrelated_repository="$test_root/unrelated"
new_repository "$unrelated_repository"
commit "$unrelated_repository" "unrelated commit"
unrelated_commit="$(git -C "$unrelated_repository" rev-parse HEAD)"
git -C "$v3_repository" fetch --quiet "$unrelated_repository" "$unrelated_commit"
if run_version "$v3_repository" branch v3 "$test_root/v3-unrelated.output" \
  MNAMER_V3_FIRST_COMMIT="$unrelated_commit" 2>/dev/null; then
  echo "Expected a non-ancestor v3 anchor to fail." >&2
  exit 1
fi

if run_version "$v3_repository" branch v3 "$test_root/v3-missing.output" \
  MNAMER_V3_FIRST_COMMIT=0000000000000000000000000000000000000000 2>/dev/null; then
  echo "Expected a missing v3 anchor to fail." >&2
  exit 1
fi

main_repository="$test_root/main"
new_repository "$main_repository"
commit "$main_repository" "stable release"

output="$test_root/main-untagged.output"
run_version "$main_repository" branch main "$output"
assert_output "$output" "publish=false"
assert_no_version "$output"

git -C "$main_repository" tag v3.0.0
output="$test_root/main-tagged.output"
run_version "$main_repository" branch main "$output"
assert_output "$output" "publish=false"
assert_no_version "$output"

output="$test_root/stable-tag.output"
run_version "$main_repository" tag v3.0.0 "$output"
assert_output "$output" "version=3.0.0"
assert_output "$output" "channel=release"

if run_version "$main_repository" tag v3.0 "$test_root/malformed-tag.output" 2>/dev/null; then
  echo "Expected a malformed stable tag to fail." >&2
  exit 1
fi

commit "$main_repository" "begin 3.0.1 development"
output="$test_root/main-first.output"
run_version "$main_repository" branch main "$output"
assert_output "$output" "version=3.0.1-dev1"

commit "$main_repository" "continue 3.0.1 development"
output="$test_root/main-second.output"
run_version "$main_repository" branch main "$output"
assert_output "$output" "version=3.0.1-dev2"

merge_repository="$test_root/main-merge"
new_repository "$merge_repository"
commit "$merge_repository" "stable release"
git -C "$merge_repository" tag v3.0.0
git -C "$merge_repository" switch --quiet --create topic
commit "$merge_repository" "topic commit one"
commit "$merge_repository" "topic commit two"
git -C "$merge_repository" switch --quiet main
git -C "$merge_repository" merge --quiet --no-ff topic --message "merge topic"
output="$test_root/main-merge.output"
run_version "$merge_repository" branch main "$output"
assert_output "$output" "version=3.0.1-dev1"

output="$test_root/published.output"
GITHUB_OUTPUT="$output" MNAMER_REGISTRY_STATUS=200 bash "$published_script" 3.0.0-dev1
assert_output "$output" "published=true"

output="$test_root/unpublished.output"
GITHUB_OUTPUT="$output" MNAMER_REGISTRY_STATUS=404 bash "$published_script" 3.0.0-dev1
assert_output "$output" "published=false"

if GITHUB_OUTPUT="$test_root/registry-error.output" MNAMER_REGISTRY_STATUS=500 \
  bash "$published_script" 3.0.0-dev1 2>/dev/null; then
  echo "Expected an unexpected registry response to fail." >&2
  exit 1
fi

repository_root="$(git -C "$script_dir" rev-parse --show-toplevel)"
output="$test_root/current-v3.output"
run_version "$repository_root" branch v3 "$output"
assert_output "$output" "version=3.0.0-dev4"

echo "Package version tests passed."
