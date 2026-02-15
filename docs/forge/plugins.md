# Forge Plugins and Subpages

Forge is extensible through payload plugins and documentation subpages.

## User View

- Plugins add new payload kinds visible in `reach forge --list`.
- Forge can be used as a payload generator only, or combined with Core route creation.

## Dev

Plugin layout:

- `forge_plugins/<family>/<name>.py`
- Implement `generate(**kwargs)` for payload generation.

Operational notes:

- Keep payload docs in dedicated subpages (like this page and `payloads.md`) so users can find usage quickly.
- When adding a new payload family, add:
  - plugin code
  - examples in docs
  - nav entry in `mkdocs.yml` if it needs a dedicated page
