# REACH overview

REACH is a modular framework for hosting external payloads and capturing callbacks during authorized security testing. Its core is a dynamic routing and logging system backed by a database, with separate public and admin surfaces.

Pillars:
- Dynamic HTTP routing for external payloads
- Centralized request logging for correlation and analysis
- Protocol extensions (HTTP, FTP, WSS, DNS) that feed the same logging store
- Admin API for managing routes, rules, logs, and DNS zones

Typical workflow:
1) Start the core servers (public and admin).
2) Create dynamic routes or payloads.
3) Observe and correlate requests via logs.
4) Run DNS for OOB callbacks using DB-backed zones.

See the component docs for details:
- `servers.md`
- `dns.md`
- `logs.md`
- `forge.md`
- `config.md`
