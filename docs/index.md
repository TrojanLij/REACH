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
- Core protocol handlers (HTTP, FTP, WSS)
- Optional DNS add-on tool for OOB DNS callbacks

## User View

### Share in 30 seconds

REACH helps red teams run callback infrastructure in a structured way:

- expose payload and callback endpoints quickly
- capture inbound traffic centrally across protocols
- manage routes/rules/zones from an admin API

Use only with explicit authorization and approved scope.

### Component model

Core, Forge, and CLI are modular and can run independently.

- Core: runtime/control plane and minimum required backend.
- Forge: payload generation (can run standalone, best when connected to Core).
- CLI: operator interface (many commands require reachable Core APIs).
- DNS tool: optional standalone OOB DNS service integrated with Core DB/logging.

Best results come from using them together.  
Minimum requirement for full workflow: Core must run or be reachable.

### Component interaction

```text
Forge/CLI/operator actions
          |
          v
        Core (admin API + public listeners)
          |
          v
      routes/rules/logs/zones in shared DB
```

## CORE

- [Getting Started](getting-started.md) - install, run, and verify your first callback flow
- [Architecture Overview](core/architecture.md) - understand how public, admin, DNS, and DB fit together
- [Core Runtime](core/core-runtime.md) - public vs admin responsibilities and shared state flow
- [Dynamic Routing](core/dynamic-routing.md) - route matching behavior and runtime route usage
- [Admin API Surface](core/admin-api.md) - control routes, rules, logs, and zones
- [Protocols Architecture](core/protocols/protocols.md) - protocol support and TLS edge patterns
- [Logging Pipeline](core/logging-pipeline.md) - what gets logged and how to query it
- [Persistence Layer](core/persistence-layer.md) - what REACH stores and why
- [Security Boundaries](core/security-boundaries.md) - deployment hardening and exposure controls

## FORGE

- [Forge Overview](forge/forge.md) - payload generation and Core integration
- [Payload Workflows](forge/payloads.md) - practical payload creation patterns
- [Plugins and Subpages](forge/plugins.md) - extend Forge with custom modules
- [Trigger Rules (IFTTT)](forge/ifttt_rules.md) - if-this-then-that automation logic

## CLI

- [CLI Overview](cli/index.md) - command map and usage model
- [Server CLI](cli/server.md) - start/manage server roles and protocols
- [Routes CLI](cli/routes.md) - inspect static and dynamic routes
- [Logs CLI](cli/logs.md) - stream and filter request logs
- [Forge CLI](cli/forge.md) - payload generation and route registration
- [DNS CLI](cli/dns.md) - run and configure DNS service
- [Dev CLI](cli/dev.md) - developer maintenance utilities

## OPERATIONS

- [Servers and Protocols](operations/servers.md) - run public/admin roles and protocol listeners
- [DNS Service](operations/dns.md) - DB-backed zone management and OOB callbacks
- [Logs](operations/logs.md) - log API and tailing workflows
- [Configuration](operations/config.md) - env/preset precedence and multi-host config
- [Deployment](operations/deployment.md) - local, multi-host, and Docker patterns
- [Troubleshooting](operations/troubleshooting.md) - common issues and fixes

## Dev

Documentation entrypoints and related modules:

- Core runtime/docs map to `reach.core.*` modules.
- Forge docs map to `reach.forge.*` and `reach.cli.forge.*`.
- CLI docs map to `reach.cli.*`.
- Main CLI entrypoint is `reach.cli.main`.
