# Configuration and deployment

REACH loads config in this order: CLI flags > preset > env/.env > defaults.

## Environment variables

- `REACH_DB_URL` - SQLAlchemy URL (use Postgres for multi-host)
- `REACH_DB_FILE` - SQLite file path (used when no DB URL)
- `REACH_DB_ECHO=1` - SQLAlchemy echo
- `REACH_FORGE_PLUGIN_PATHS` - extra plugin paths

## Presets
Presets define server layout:
```json
{
  "server": {
    "http": { "host": "0.0.0.0", "port": 9000 },
    "ftp":  { "host": "0.0.0.0", "port": 2121 },
    "wss":  { "host": "0.0.0.0", "port": 8443 },
    "role": "both",
    "log_level": "info",
    "protocol": "http"
  },
  "admin": { "host": "0.0.0.0", "port": 8001 },
  "db": {
    "url": "sqlite:///./reach_core.db",
    "echo": false
  }
}
```
Run:
```bash
reach server start --preset ./my-preset.json
```

## Multi-host deployment (Postgres)
Each service can run on its own host/IP. All of them must point to the same DB.

Example env:
```
REACH_DB_URL=postgresql://user:pass@DB_IP:5432/reach
```

Admin host:
```bash
reach server start --role admin --host ADMIN_IP --port 8001
```

Public HTTP host:
```bash
reach server start --role public --host PUBLIC_IP --port 8000
```

DNS host:
```bash
reach dns serve --host DNS_IP --port 53 --db-zones
```

See also:

- [Persistence Layer](../core/persistence-layer.md)
- [Security Boundaries](../core/security-boundaries.md)
