# Persistence Layer

The persistence layer is the shared database REACH uses for runtime state and history.

## User View

### What is stored

REACH stores the following core data:

- Dynamic routes (what public callbacks should return).
- Request logs (HTTP, WSS, FTP, DNS events).
- Trigger rules (IFTTT-style conditions/actions).
- Rule state (temporary workflow state across requests).
- DNS zones (for DB-backed DNS service).

### Why this matters

- Public and admin interfaces stay synchronized through one shared DB.
- Data persists across restarts.
- Multi-host deployments work only when services share the same DB.

### Storage flow

```text
admin updates (routes/rules/zones)
            |
            v
      shared database
            ^
            |
public handlers write logs and read current config
```

### Configuration examples

Use default local SQLite (development):

```bash
reach server start --role both --port 8000
```

Use explicit SQLite path:

```bash
REACH_DB_FILE=~/.reach/reach_core.db reach server start --role both --port 8000
```

Use Postgres (recommended for multi-host):

```bash
REACH_DB_URL=postgresql://user:pass@DB_IP:5432/reach \
reach server start --role admin --host 127.0.0.1 --port 8001
```

### Data lifecycle operations

Clear logs only:

```bash
reach dev clear-logs
```

Reset full schema (destructive):

```bash
reach dev reset-db --yes
```

## Dev

Implementation map:

- DB config/env parsing: `reach.core.db.config`.
- Engine/session factory: `reach.core.db.engine`.
- Session helpers/decorators: `reach.core.db.session`.
- Schema initialization: `reach.core.db.init`.
- ORM models: `reach.core.db.models`.
- API schemas: `reach.core.db.schemas`.

Table map:

- `routes`: dynamic route definitions.
- `request_logs`: captured protocol events.
- `trigger_rules`: stored IFTTT rules.
- `rule_state`: keyed state with optional expiration.
- `dns_zones`: DNS zone configuration.

Behavior notes:

- If `REACH_DB_URL` is set, that URL is used directly.
- Otherwise REACH uses SQLite (default file or `REACH_DB_FILE`).
- `init_db()` creates tables and is guarded to run once per process unless forced.
