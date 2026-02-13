# REACH docs

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

## Share in 30 seconds
REACH helps red teams run callback infrastructure in a structured way:
- expose payload and callback endpoints quickly
- capture inbound traffic centrally across protocols
- manage routes/rules/zones from an admin API

Use only with explicit authorization and approved scope.

## New here
- `getting-started.md` - install, run, and verify your first callback flow
- `architecture.md` - understand how public, admin, DNS, and DB fit together

## Operate REACH
- `servers.md` - start public/admin roles and protocol listeners
- `dns.md` - run DNS and manage zones from DB/admin API
- `logs.md` - stream and filter request logs
- `config.md` - env and preset precedence, multi-host setup

## Payloads and rules
- `forge.md` - generate payloads and create dynamic routes
- `ifttt_rules.md` - rule matching, templates, actions, chaining
<!-- - `ifttt_builder.html` - visual IFTTT rule builder -->

## CLI reference
- `cli/index.md` - command map and command-specific examples

## Deploy and support
- `deployment.md` - local, multi-host, Docker deployment patterns
- `troubleshooting.md` - common issues and direct fixes
