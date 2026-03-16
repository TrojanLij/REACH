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

# Optional DNS add-on (separate service, DB-backed zones), beta feature and not fully implemented
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

### DNS
You will be required to set up and point a domain at the server. 

## Disclaimer
REACH is intended for **authorized** security testing only. It should be deployed temporarily and with appropriate access controls for the engagement scope.


(yes, I used AI to generate the documentation and fix my code.... I'm lazy)