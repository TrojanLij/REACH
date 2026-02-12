#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <component> <version>"
  echo "example: $0 ui 0.0.2"
  exit 1
fi

component="$1"
new_version="$2"
versions_file="versions.toml"

if [[ ! "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9]+)?$ ]]; then
  echo "error: version must look like SemVer (for example: 1.2.3 or 1.2.3-rc1)"
  exit 1
fi

if [[ ! -f "$versions_file" ]]; then
  echo "error: missing $versions_file"
  exit 1
fi

if ! grep -Eq "^${component}[[:space:]]*=" "$versions_file"; then
  echo "error: component '${component}' not found in $versions_file"
  exit 1
fi

sed -Ei "s|^(${component}[[:space:]]*=[[:space:]]*\").*(\")$|\\1${new_version}\\2|" "$versions_file"

if [[ "$component" == "core" ]]; then
  sed -Ei "s|^(version[[:space:]]*=[[:space:]]*\").*(\")$|\\1${new_version}\\2|" pyproject.toml
fi

if [[ "$component" == "ui" ]]; then
  sed -Ei "s|^(  \"version\": \").*(\",)$|\\1${new_version}\\2|" ui/reach-ui/package.json
fi

echo "updated ${component} -> ${new_version}"
