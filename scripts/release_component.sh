#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ./scripts/release_component.sh <component> [--dry-run] [--commit] [--tag]

Examples:
  ./scripts/release_component.sh ui --dry-run
  ./scripts/release_component.sh core --commit
  ./scripts/release_component.sh core --commit --tag

Rules:
  - Uses commit history since the latest tag matching <component>/v*
  - Detects bump type from Conventional Commits:
    * major: "!" in type/scope OR "BREAKING CHANGE" in body
    * minor: "feat:"
    * patch: everything else with commits
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

component="$1"
shift

dry_run=0
do_commit=0
do_tag=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      ;;
    --commit)
      do_commit=1
      ;;
    --tag)
      do_tag=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument '$1'"
      usage
      exit 1
      ;;
  esac
  shift
done

if [[ "$dry_run" -eq 1 && "$do_commit" -eq 1 ]]; then
  echo "error: --dry-run cannot be combined with --commit"
  exit 1
fi

if [[ "$do_tag" -eq 1 && "$do_commit" -ne 1 ]]; then
  echo "error: --tag requires --commit so the tag includes release files"
  exit 1
fi

versions_file="versions.toml"
if [[ ! -f "$versions_file" ]]; then
  echo "error: missing $versions_file"
  exit 1
fi

if ! grep -Eq "^${component}[[:space:]]*=" "$versions_file"; then
  echo "error: unknown component '${component}' in $versions_file"
  exit 1
fi

current_version="$(awk -F'"' -v c="$component" '$1 ~ "^" c "[[:space:]]*=" {print $2}' "$versions_file")"
if [[ -z "$current_version" ]]; then
  echo "error: failed to parse current version for ${component}"
  exit 1
fi

component_paths=()
case "$component" in
  core)
    component_paths=("src/reach/core" "src/reach/__init__.py" "pyproject.toml")
    ;;
  cli)
    component_paths=("src/reach/cli" "tests/cli")
    ;;
  forge)
    component_paths=("src/reach/forge" "plugins/forge")
    ;;
  dns)
    component_paths=("src/reach/dns" "docs/dns.md")
    ;;
  ui)
    component_paths=("ui/reach-ui")
    ;;
  ifttt_plugin)
    component_paths=("plugins/IFTTT" "docs/ifttt_rules.md")
    ;;
  *)
    component_paths=(".")
    ;;
esac

last_tag="$(git tag --list "${component}/v*" --sort=-version:refname | head -n1 || true)"
log_range="HEAD"
if [[ -n "$last_tag" ]]; then
  log_range="${last_tag}..HEAD"
fi

log_output="$(git log --reverse --format='%h%x1f%s%x1f%b%x1e' "$log_range" -- "${component_paths[@]}")"
if [[ -z "$log_output" ]]; then
  echo "No commits found for component '${component}' in paths: ${component_paths[*]}"
  exit 0
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

breaking_file="${tmp_dir}/breaking.txt"
feat_file="${tmp_dir}/feat.txt"
fix_file="${tmp_dir}/fix.txt"
refactor_file="${tmp_dir}/refactor.txt"
docs_file="${tmp_dir}/docs.txt"
other_file="${tmp_dir}/other.txt"
all_file="${tmp_dir}/all.txt"

bump_level=0

append_line() {
  local file="$1"
  local hash="$2"
  local subject="$3"
  printf -- "- %s (%s)\n" "$subject" "$hash" >> "$file"
  printf -- "- %s (%s)\n" "$subject" "$hash" >> "$all_file"
}

while IFS= read -r -d $'\x1e' entry; do
  [[ -z "$entry" ]] && continue

  IFS=$'\x1f' read -r hash subject body <<< "$entry"
  normalized_subject="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"

  is_breaking=0
  if printf '%s' "$subject" | grep -Eq '^[[:alpha:]]+(\([^)]+\))?!:' || [[ "$body" == *"BREAKING CHANGE"* ]]; then
    is_breaking=1
  fi

  if [[ "$is_breaking" -eq 1 ]]; then
    append_line "$breaking_file" "$hash" "$subject"
    bump_level=3
    continue
  fi

  if printf '%s' "$normalized_subject" | grep -Eq '^feat(\([^)]+\))?:'; then
    append_line "$feat_file" "$hash" "$subject"
    if [[ "$bump_level" -lt 2 ]]; then
      bump_level=2
    fi
    continue
  fi

  if printf '%s' "$normalized_subject" | grep -Eq '^(fix|perf)(\([^)]+\))?:'; then
    append_line "$fix_file" "$hash" "$subject"
    if [[ "$bump_level" -lt 1 ]]; then
      bump_level=1
    fi
    continue
  fi

  if printf '%s' "$normalized_subject" | grep -Eq '^refactor(\([^)]+\))?:'; then
    append_line "$refactor_file" "$hash" "$subject"
    if [[ "$bump_level" -lt 1 ]]; then
      bump_level=1
    fi
    continue
  fi

  if printf '%s' "$normalized_subject" | grep -Eq '^docs(\([^)]+\))?:'; then
    append_line "$docs_file" "$hash" "$subject"
    if [[ "$bump_level" -lt 1 ]]; then
      bump_level=1
    fi
    continue
  fi

  append_line "$other_file" "$hash" "$subject"
  if [[ "$bump_level" -lt 1 ]]; then
    bump_level=1
  fi
done < <(printf '%s' "$log_output")

if [[ "$bump_level" -eq 0 ]]; then
  echo "No version-impacting commits detected for '${component}'."
  exit 0
fi

core_version="${current_version%%[-+]*}"
if [[ ! "$core_version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  echo "error: current version '${current_version}' is not SemVer x.y.z"
  exit 1
fi

major="${BASH_REMATCH[1]}"
minor="${BASH_REMATCH[2]}"
patch="${BASH_REMATCH[3]}"

case "$bump_level" in
  3)
    major=$((major + 1))
    minor=0
    patch=0
    bump_kind="major"
    ;;
  2)
    minor=$((minor + 1))
    patch=0
    bump_kind="minor"
    ;;
  *)
    patch=$((patch + 1))
    bump_kind="patch"
    ;;
esac

next_version="${major}.${minor}.${patch}"
today="$(date +%F)"
changelog_file="CHANGELOG.${component}.md"
section_file="${tmp_dir}/section.md"

{
  echo "## v${next_version} - ${today}"
  echo

  if [[ -s "$breaking_file" ]]; then
    echo "### Breaking Changes"
    cat "$breaking_file"
    echo
  fi
  if [[ -s "$feat_file" ]]; then
    echo "### Features"
    cat "$feat_file"
    echo
  fi
  if [[ -s "$fix_file" ]]; then
    echo "### Fixes"
    cat "$fix_file"
    echo
  fi
  if [[ -s "$refactor_file" ]]; then
    echo "### Refactors"
    cat "$refactor_file"
    echo
  fi
  if [[ -s "$docs_file" ]]; then
    echo "### Docs"
    cat "$docs_file"
    echo
  fi
  if [[ -s "$other_file" ]]; then
    echo "### Other"
    cat "$other_file"
    echo
  fi
} > "$section_file"

echo "Component:       ${component}"
echo "Last tag:        ${last_tag:-<none>}"
echo "Current version: ${current_version}"
echo "Bump type:       ${bump_kind}"
echo "Next version:    ${next_version}"

if [[ "$dry_run" -eq 1 ]]; then
  echo
  echo "[dry-run] Changelog preview:"
  sed -n '1,120p' "$section_file"
  exit 0
fi

./scripts/bump_component_version.sh "$component" "$next_version"

if [[ ! -f "$changelog_file" ]]; then
  {
    echo "# Changelog (${component})"
    echo
  } > "$changelog_file"
fi

{
  sed -n '1,2p' "$changelog_file"
  cat "$section_file"
  sed -n '3,999999p' "$changelog_file"
} > "${tmp_dir}/new_changelog.md"
mv "${tmp_dir}/new_changelog.md" "$changelog_file"

echo "updated ${changelog_file}"

files_to_commit=("$versions_file" "$changelog_file")
if [[ "$component" == "core" ]]; then
  files_to_commit+=("pyproject.toml")
fi
if [[ "$component" == "ui" ]]; then
  files_to_commit+=("ui/reach-ui/package.json")
fi

if [[ "$do_commit" -eq 1 ]]; then
  git add "${files_to_commit[@]}"
  git commit -m "chore(release): ${component} v${next_version}" -- "${files_to_commit[@]}"
  echo "created commit: chore(release): ${component} v${next_version}"

  if [[ "$do_tag" -eq 1 ]]; then
    git tag -a "${component}/v${next_version}" -m "release ${component} v${next_version}"
    echo "created tag: ${component}/v${next_version}"
  fi
else
  echo "release files updated but not committed."
  echo "next:"
  echo "  git add ${files_to_commit[*]}"
  echo "  git commit -m 'chore(release): ${component} v${next_version}'"
  echo "  git tag -a '${component}/v${next_version}' -m 'release ${component} v${next_version}'"
fi
