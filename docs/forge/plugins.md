# Forge Plugins and Subpages

Forge is extensible through generator plugins and documentation subpages.

## User View

- Plugins add new generator kinds visible in `reach forge --list`.
- Forge can be used as a generator module only, or combined with Core route creation.

## Dev

Plugin layout:

- `plugins/forge/generators/<family>/<name>.py`
- `plugins/forge/exploits/<family>/<name>.py`
- Each plugin file should declare a `PLUGIN` metadata dict and an entrypoint function.

Example plugin metadata:

```python
PLUGIN = {
    "api_version": "1",
    "type": "generator",  # or "exploit"
    "kind": "xss_basic",
    "entrypoint": "generate",  # or "run" for exploit modules
    "summary": "Short description",
    "requires_python": [],
    "requires_system": [],
}
```

Operational notes:

- Keep generator docs in dedicated subpages (like this page and `generators.md`) so users can find usage quickly.
- When adding a new generator family, add:
  - plugin code
  - examples in docs
  - nav entry in `mkdocs.yml` if it needs a dedicated page
