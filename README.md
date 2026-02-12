# REACH

```python
   ____    _____      _      ____   _   _ 
  |  _ \  | ____|    / \    / ___| | | | |
  | |_) | |  _|     / _ \  | |     | |_| |
  |  _ < _| |___ _ / ___ \ | |___ _|  _  |
  |_| \_(_)_____(_)_/   \_(_)____(_)_| |_|
  
  Request Engine for Attacks, Callbacks & Handling
  --@TrojanLij
```

**R.E.A.C.H. - Request Engine for Attacks, Callbacks & Handling**

REACH is a modular web exploitation framework for authorized security testing. It provides a dynamic routing core for hosting external payloads and capturing callbacks, with structured request logging and extensible protocol support.

Key ideas:
- Dynamic HTTP routes managed at runtime
- Centralized request logging for OOB workflows
- Separate public/admin surfaces
- Protocol extensions (HTTP, FTP, WSS, DNS)

## Share in 30 seconds
REACH helps red teams run callback infrastructure in a structured way:
- expose payload and callback endpoints quickly
- capture inbound traffic centrally across protocols
- manage routes/rules/zones from an admin API

Use only with explicit authorization and approved scope.

## Documentation
Start here:
- `docs/index.md` - docs hub by workflow
- `docs/getting-started.md` - first run in under 10 minutes
- `docs/architecture.md` - component map and data flow

Operations and components:
- `docs/servers.md` - public/admin servers and protocol handling
- `docs/dns.md` - DNS service, zones, and admin API
- `docs/logs.md` - request logging and tailing
- `docs/forge.md` - payload generation
- `docs/config.md` - env/presets and multi-host deployment
- `docs/ifttt_rules.md` - IFTTT rule model

Reference and support:
- `docs/cli/index.md` - command groups and examples
- `docs/deployment.md` - local, multi-host, and Docker patterns
- `docs/troubleshooting.md` - common failures and fixes

Build and preview docs locally:
```bash
python -m pip install -e ".[docs]"
mkdocs serve
```
Then open `http://127.0.0.1:8000`.

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

## Disclaimer
REACH is intended for **authorized** security testing only. It should be deployed temporarily and with appropriate access controls for the engagement scope.
