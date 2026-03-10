![Python 3.12 & latest](https://github.com/TrojanLij/REACH/actions/workflows/e2e-tests.yml/badge.svg?branch=main)
![Release](https://github.com/TrojanLij/REACH/actions/workflows/release.yml/badge.svg?branch=main)

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
- Core protocol handlers (HTTP, FTP, WSS)
- Optional DNS add-on tool for OOB DNS workflows

## Share in 30 seconds
REACH helps red teams run callback infrastructure in a structured way:
- expose payload and callback endpoints quickly
- capture inbound traffic centrally across protocols
- manage routes/rules/zones from an admin API

Use only with explicit authorization and approved scope.

## Install

Clone the repository:

```bash
git clone https://github.com/TrojanLij/REACH
cd REACH
```

Install REACH in editable mode:

```bash
python -m pip install -e .
```

## Documentation
Start here:
- `docs/index.md` - docs hub by workflow
- `docs/getting-started.md` - first run in under 10 minutes
- `docs/core/architecture.md` - component map and data flow

Operations and components:
- `docs/core/core-runtime.md` - public/admin core runtime model
- `docs/core/protocols/protocols.md` - protocol support and architecture
- `docs/operations/servers.md` - public/admin servers and protocol handling
- `docs/operations/dns.md` - optional DNS add-on tool, zones, and admin API
- `docs/operations/logs.md` - request logging and tailing
- `docs/forge/forge.md` - Forge overview
- `docs/operations/config.md` - env/presets and multi-host deployment
- `docs/forge/ifttt_rules.md` - IFTTT rule model

Reference and support:
- `docs/cli/index.md` - command groups and examples
- `docs/operations/deployment.md` - local, multi-host, and Docker patterns
- `docs/operations/troubleshooting.md` - common failures and fixes

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

# Optional DNS add-on (separate service, DB-backed zones)
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

## Disclaimer
REACH is intended for **authorized** security testing only. It should be deployed temporarily and with appropriate access controls for the engagement scope.
