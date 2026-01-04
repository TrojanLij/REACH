# REACH

Lightweight FastAPI core plus a Typer-based CLI for spinning up dynamic routes during pentests.

## Core (FastAPI apps)
- Factories: `reach.core.server:create_public_app` (dynamic routes) and `reach.core.server:create_admin_app` (admin APIs/logs). Import the factories and compose them; nothing runs at import time.
- DB init: call `reach.core.server.init_db()` once per run (the CLI does this for you) to create tables. Backed by SQLite by default, override with `REACH_DB_URL` or `REACH_DB_FILE`.
- Admin APIs (admin app): `/api/routes` (CRUD dynamic routes), `/api/logs` (stream request logs), `/api/health`, `/debug/routes`. Protect or keep separate from the public app.
- Public app: catch-all dynamic router serving DB-backed routes; blocks reserved prefixes (`/api/*`, `/debug/*`).

## CLI
- Preferred (via uv / console script): `reach server start --role both` (or `reach ...` for other subcommands).
- Alternative module entry: `python -m reach.cli.main ...` (same commands/flags).

### Server
- `server start [--host 0.0.0.0] [--port 8000] [--role public|admin|both] [--port-public N] [--port-admin N] [--reload] [--log-level info]`
  - Uses the FastAPI factories via uvicorn factory mode and calls `init_db()` before boot.
  - `role=public` (default): dynamic routes on `--port`.
  - `role=admin`: admin APIs on `--port`.
  - `role=both`: runs public on `--port-public` (or `--port`), admin on `--port-admin` (or `--port+1`).

### Routes
- `routes list [--show-body] [--full-body] [--decode/--raw]` — list all static + dynamic routes.
- `routes static` — list only static FastAPI routes.
- `routes dynamic [--show-body] [--full-body] [--decode/--raw]` — list DB-backed routes.

### Logs
- `logs tail [--core-url http://127.0.0.1:8000] [--interval 1.0] [--once] [--regex "..."]` — poll `/api/logs` and stream matching entries.

### Dev utilities
- `dev reset-db [-y]` — drop and recreate all tables (destroys data).
- `dev clear-logs` — wipe request logs.

### Presets
- You can pass a JSON preset to `reach server start` to avoid long flag lists:
  ```json
  {
    "server": {
      "role": "both",
      "public": {"host": "0.0.0.0", "port": 8000},
      "admin": {"host": "0.0.0.0", "port": 8080},
      "reload": false,
      "log_level": "info"
    }
  }
  ```
  Run: `reach server start --preset ./my-preset.json`
  - CLI flags still override the preset when provided (e.g., `--port-public`).

## Configuration (env)
- `REACH_DB_URL` — full SQLAlchemy URL; if set, overrides SQLite.
- `REACH_DB_FILE` — path to SQLite file (used when no `REACH_DB_URL`).
- `REACH_DB_ECHO=1` — enable SQLAlchemy echo for debugging.

## Minimal local run
```bash
# Preferred (uv / installed script)
reach server start --role both --port 8000
# Public: http://127.0.0.1:8000  Admin: http://127.0.0.1:8001
reach routes list
reach logs tail --core-url http://127.0.0.1:8001 --once

# Alternate module entry
python -m reach.cli.main server start --role both --port 8000
python -m reach.cli.main routes list
python -m reach.cli.main logs tail --core-url http://127.0.0.1:8001 --once
```

## Development / embedding the core
- Install in editable mode inside your venv: `pip install -e .` (then use the `reach` entrypoint).
- Programmatic attach: call `init_db()` once, then build apps from the factories:
  ```python
  from reach.core.server import init_db, create_public_app, create_admin_app

  init_db()
  public_app = create_public_app()
  admin_app = create_admin_app()  # optional, for admin APIs/logs
  ```
  Mount either app into your own ASGI stack, or serve with uvicorn: `uvicorn reach.core.server:create_public_app --factory --port 8000`.
- Client access: use the thin HTTP client for admin APIs:
  ```python
  from reach.core.client import CoreClient
  client = CoreClient("http://127.0.0.1:8001")
  routes = client.list_routes()
  ```
