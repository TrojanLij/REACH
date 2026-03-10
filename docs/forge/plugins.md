# Forge Plug-and-Play Packages

Forge plugins are packaged as one self-contained folder.

This applies to community plugins and built-ins.

## Package Layout

Canonical root:

- `plugins/forge/exploits/<category>/<item_name>/`
- `plugins/forge/generators/<category>/<item_name>/`
- `plugins/forge/plugins/<category>/<item_name>/`

Minimum files:

- `manifest.yaml` (required)
- `src/entry.py` (required)
- `README.md` (required)
- `requirements.txt` (recommended default)

Optional files and folders:

- `system-requirements.txt`
- `assets/` (or other directories declared in `asset_dirs`)
- `tests/`
- `examples/`

## Manifest Contract

### Required Keys

- `id`: globally unique plugin id, immutable after release
- `type`: `exploit`, `generator`, or `plugin`
- `name`: display name
- `version`: plugin version (`0.1.0`, etc.)
- `forge_api_version`: current loader contract version (currently `"1"`)
- `entry`: relative path to entry module (example: `src/entry.py`)
- `entrypoint`: callable name in entry module (example: `run` or `generate`)

### Common Optional Keys

- `description`: long description
- `summary`: short description
- `category`: grouping/family (example: `web`, `xss`, `xxe`)
- `kind`: CLI/runtime kind; if omitted, derived from `<category>_<folder_name>`
- `author`
- `license`
- `tags`: list of labels
- `requires_python`: list of Python dependency specs
- `requires_system`: list of system/runtime dependencies
- `requirements_file`: defaults to `requirements.txt` if present
- `system_requirements_file`: defaults to `system-requirements.txt` if present
- `required_env`: required environment variable names
- `optional_env`: optional environment variable names
- `asset_dirs`: list of extra package directories (example: `["assets", "templates"]`)
- `min_core_version`
- `max_core_version`

Validation rules:

- `required_env` and `optional_env` must be `list[str]`.
- The same env var cannot appear in both lists.
- Env names must match identifier format (`[A-Za-z_][A-Za-z0-9_]*`).
- Referenced files/dirs must resolve inside the package root.

## Manifest Example (Exploit)

```yaml
id: web.local_storage_replay
type: exploit
name: Local Storage Replay
version: 0.1.0
forge_api_version: "1"
category: web
kind: web_local_storage_replay
entry: src/entry.py
entrypoint: run
summary: Replay localStorage keys before first navigation with Playwright.
description: Replay localStorage keys before first navigation with Playwright.
requirements_file: requirements.txt
system_requirements_file: system-requirements.txt
requires_python:
  - playwright>=1.40
requires_system:
  - playwright install
required_env: []
optional_env:
  - PLAYWRIGHT_BROWSERS_PATH
asset_dirs:
  - assets
```

## Manifest Example (Generator)

```yaml
id: xss.gh0st
type: generator
name: Gh0st XSS
version: 0.1.0
forge_api_version: "1"
category: xss
kind: xss_gh0st
entry: src/entry.py
entrypoint: generate
summary: Gh0st XSS payload to execute commands.
requirements_file: requirements.txt
system_requirements_file: system-requirements.txt
requires_python: []
requires_system: []
required_env: []
optional_env: []
asset_dirs:
  - assets
```

## Entrypoint Design

Exploit entrypoint pattern:

```python
def run(*, origin: str, keep_open: str = "false", **kwargs) -> dict[str, object]:
    ...
```

Generator entrypoint pattern:

```python
def generate(callback_url: str | None = None, tags: bool = False) -> str:
    ...
```

Guidelines:

- Keep one callable entrypoint (`run` for exploit, `generate` for generator).
- Parse string CLI values in exploit handlers where needed.
- Return structured dicts for exploits and strings for generators.
- Document parameters clearly in docstrings (`Params:` block) for CLI help rendering.

## CLI Workflow

Create scaffold:

```bash
reach forge scaffold generator my_payload \
  --id demo.my_payload \
  --category demo
```

Validate package root:

```bash
reach forge validate --root plugins/forge
reach forge validate --root src/reach/forge
```

Reorganize packages into canonical type/category layout:

```bash
reach forge cleanup --source-root forge --destination-root plugins/forge --dry-run
reach forge cleanup --source-root forge --destination-root plugins/forge --apply
```
