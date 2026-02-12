```python
   ____    _____      _      ____   _   _ 
  |  _ \  | ____|    / \    / ___| | | | |
  | |_) | |  _|     / _ \  | |     | |_| |
  |  _ < _| |___ _ / ___ \ | |___ _|  _  |
  |_| \_(_)_____(_)_/   \_(_)____(_)_| |_|
  
  Request Engine for Attacks, Callbacks & Handling
  --@TrojanLij
```

REACH is a modular web exploitation framework for authorized security testing. It provides a dynamic routing core for hosting external payloads and capturing callbacks, with structured request logging and extensible protocol support.

Key ideas:
- Dynamic HTTP routes managed at runtime
- Centralized request logging for OOB workflows
- Separate public/admin surfaces
- Protocol extensions (HTTP, FTP, WSS, DNS)

## Documentation
- `docs/overview.md` - project goals and architecture
- `docs/servers.md` - public/admin servers and protocol handling
- `docs/dns.md` - DNS service, zones, and admin API
- `docs/logs.md` - request logging and tailing
- `docs/forge.md` - payload generation
- `docs/config.md` - env/presets and multi-host deployment
- `docs/ifttt_rules.md` - IFTTT rule model

## Quick start
```bash
# Public + admin (single host)
reach server start --role both --port 8000

# DNS (separate service, DB-backed zones)
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

## Component versions
REACH tracks component versions in `versions.toml`.

- Show runtime + component versions:
```bash
reach version
```
- Show one component:
```bash
reach version --component ui
```
- Bump a component:
```bash
./scripts/bump_component_version.sh ui 0.0.2
```
  - Bumping `core` also updates `pyproject.toml` package version.
  - Bumping `ui` also updates `ui/reach-ui/package.json`.

### Auto release + changelog
Use commit history to infer bump type and generate a per-component changelog entry.

- Preview the next release without modifying files:
```bash
./scripts/release_component.sh ui --dry-run
```
- Apply bump + changelog files (no commit/tag):
```bash
./scripts/release_component.sh ui
```
- Apply and create release commit + tag:
```bash
./scripts/release_component.sh ui --commit --tag
```

Conventional Commit bump rules:
- `major`: commit subject with `!` (example `feat(core)!:`) or body with `BREAKING CHANGE`
- `minor`: `feat:`
- `patch`: all other commit types with changes

### GitHub release workflow
The repository includes `.github/workflows/release.yml`:
- Trigger on pushed component tags (`core/v*`, `ui/v*`, etc.)
- Validate tag version matches `versions.toml`
- Run component smoke checks (`pytest` for backend components, `npm build` for UI)
- Create a GitHub Release and pull notes from `CHANGELOG.<component>.md`

Recommended release flow:
```bash
# 1) Preview the next release
./scripts/release_component.sh ui --dry-run

# 2) Apply bump + changelog + commit + tag
./scripts/release_component.sh ui --commit --tag

# 3) Push commit and tag to trigger release workflow
git push origin main --follow-tags
```

## Disclaimer
REACH is intended for **authorized** security testing only. It should be deployed temporarily and with appropriate access controls for the engagement scope.
