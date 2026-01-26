# REACH

**R.E.A.C.H. - Request Engine for Attacks, Callbacks & Handling**

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

## Disclaimer
REACH is intended for **authorized** security testing only. It should be deployed temporarily and with appropriate access controls for the engagement scope.
