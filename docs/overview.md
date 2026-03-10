# REACH overview

This is the legacy high-level overview page.  
For the full structured docs map, use [Home](index.md).

## User View

REACH is a modular framework for hosting external payloads and capturing callbacks during authorized security testing.

Core pillars:

- Dynamic HTTP routing for external payload delivery/callback handling.
- Centralized request logging for correlation and analysis.
- Core protocol handlers (HTTP, FTP, WSS) feeding one shared log/data model.
- Optional DNS add-on tool for OOB DNS workflows.
- Admin API for managing routes, rules, logs, and DNS zones.

Typical workflow:

1. Start Core services (public/admin).
2. Create dynamic routes or payload-backed routes.
3. Observe and correlate inbound requests via logs.
4. Optionally run DNS service for OOB callbacks using DB-backed zones.

### Related docs

- [Servers and Protocols](operations/servers.md)
- [DNS Service](operations/dns.md)
- [Logs](operations/logs.md)
- [Forge Overview](forge/forge.md)
- [Configuration](operations/config.md)

## Dev

Legacy overview mapped to current module areas:

- Core runtime and APIs: `reach.core.*`
- Protocol handlers: `reach.core.protocols.*`, `reach.dns.server`
- CLI/operator layer: `reach.cli.*`
- Forge generator/exploit workflows: `reach.forge.*`, `reach.cli.forge.*`
