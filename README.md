# REACH

**R.E.A.C.H. - Request Engine for Attacks, Callbacks & Handling**

REACH is a lightweight, extensible web exploitation framework designed for penetration testers and security researchers. It provides a dynamic routing core that allows operators to create, modify, and remove HTTP routes at runtime without restarting the service, making it well suited for live assessments and collaborative testing environments.

REACH is an external tooling framework designed to enable penetration testers to rapidly deploy web-accessible assets for testing external callbacks, out-of-band interactions, and externally loaded payloads during external penetration tests and web application security assessments.

The project is built around a FastAPI-based core with a Typer-powered CLI, enabling both programmatic embedding and standalone operation. REACH separates public-facing traffic handling from administrative control surfaces, allowing testers to expose payload endpoints in a controlled manner while retaining full control over route management, request logging, and analysis.

The framework is intended for authorized security testing only and is built to integrate into existing toolchains and assessment workflows with minimal friction.

---

## REACH in the Payload Chain

REACH is designed to augment existing penetration testing workflows, not replace established tooling. In particular, it complements out-of-band (OOB) testing capabilities provided by platforms such as Burp Suite.

While generalized OOB services (e.g., Burp Collaborator) are highly effective for detecting outbound interactions, they intentionally provide limited control over response behavior. Testers cannot customize HTTP methods, response bodies, headers, status codes, or application-specific behavior for external endpoints.

REACH addresses this gap by allowing testers to deploy highly customizable, tester-controlled external endpoints. Dynamic routes can be created and modified at runtime to precisely control how an external resource responds when accessed by the target application or client. This enables more accurate validation of execution paths, interaction logic, and application behavior under realistic conditions.

In practice, REACH functions as an additional tool in the payload chain, enabling rapid deployment and teardown of customizable external endpoints to support specific testing scenarios alongside existing OOB and collaboration services.

---

## Key Features

REACH is designed to provide fine-grained control over external, tester-controlled web assets used during authorized security testing. Its primary value lies in enabling rapid iteration and customization of external endpoints that form part of a payload or callback chain.

### Dynamic Route Management
- Create, modify, and remove HTTP routes at runtime without restarting the service
- Define routes using any HTTP method (GET, POST, PUT, DELETE, etc.)
- Deploy or tear down endpoints instantly via the admin API or CLI

### Highly Customizable Responses
- Configure response bodies dynamically
- Return responses as plain text, Base64-encoded content, or structured data
- Control HTTP status codes (e.g., returning non-standard responses such as `418` instead of `200`)
- Set custom headers and response metadata

### Content-Type & Payload Control
- Explicitly define response content types (e.g. `text/plain`, `application/json`, `image/png`, `image/svg+xml`)
- Serve non-text responses such as images or other binary assets
- Support scenarios where specific content handling behavior must be validated by the target application or client

### Rapid Iteration During Live Testing
- Routes can be altered on the fly to adjust behavior as testing progresses
- Payload hosting does not require modifying files, rebuilding containers, or restarting services
- Designed to support fast feedback loops during live engagements

### Request Logging & Data Collection
- Capture inbound requests to dynamic routes in a structured manner
- Log headers, query parameters, and request metadata for analysis
- Logging can be used to observe and correlate outbound application behavior during testing
- Supports controlled collection of interaction data within the scope of an authorized engagement

### Separation of Concerns
- Public-facing routes are isolated from administrative control surfaces
- Administrative APIs and logging interfaces can be bound to separate interfaces or ports
- Supports clearer separation of responsibilities in environments where limited external exposure is required

---

## External Callback Validation (e.g. XSS, SSRF, XXE)

During external penetration tests or web application security reviews, it is often necessary to validate whether an application performs outbound interactions, such as loading external resources or executing callbacks.

In these scenarios, REACH can be deployed on a tester-controlled server and used to rapidly create web-accessible endpoints for payload hosting and callback observation. Dynamic routes can be defined at runtime (via the API or CLI) to serve test payloads or capture inbound requests without restarting the service.

For example, when testing for client-side injection or out-of-band interaction behavior, a tester may:
- Deploy REACH on external infrastructure under their control
- Create a dynamic route that serves a test payload or logs inbound requests
- Reference that route from within the target application input
- Observe and correlate incoming requests via the REACH logging interface

This approach allows testers to validate execution paths, callback behavior, and outbound connectivity in a controlled and auditable manner.

---

## Disclaimer

REACH is an **actively developed** project and should be considered **experimental**. While it is built by security practitioners for security practitioners, it is **not intended to be exposed as a permanent or publicly accessible service**. The intent behind this project is to allow security practitioners to quickly spin up auxiliary tooling for web application penetration testing, including handling dynamic routes, external callbacks, and payload delivery during an active engagement.

REACH is designed to be deployed **temporarily and in a controlled environment** for the duration of an authorized security engagement. Operators are expected to tear down instances after use and restrict network exposure to only what is required for the scope of the assessment. Running REACH on the public internet without proper isolation, access controls, and monitoring may introduce unnecessary risk.

The authors assume **no responsibility for misuse, misconfiguration, or unintended exposure**. Users are solely responsible for ensuring they have explicit authorization to deploy and operate REACH and that it is used in compliance with applicable laws, contracts, and engagement scopes.

# Structure
This project is highly modular with and is comprised of the following components.

## Core (FastAPI apps)
As the name intales' this is the core of the project. Everything revolves round this:
- Factories: `reach.core.server:create_public_app` (dynamic routes) and `reach.core.server:create_admin_app` (admin APIs/logs). Import the factories and compose them; nothing runs at import time.
- DB init: call `reach.core.server.init_db()` once per run (the CLI does this for you) to create tables. Backed by SQLite by default, override with `REACH_DB_URL` or `REACH_DB_FILE`.
- Admin APIs (admin app): `/api/routes` (CRUD dynamic routes), `/api/logs` (stream request logs), `/api/health`, `/debug/routes`. Protect or keep separate from the public app.
- Public app: catch-all dynamic router serving DB-backed routes; blocks reserved prefixes (`/api/*`, `/debug/*`).

## CLI
So not everything needs to be done via the admin api
- Preferred (via uv / console script): `reach server start --role both` (or `reach ...` for other subcommands).
- Alternative module entry: `python -m reach.cli.main server ...` (same commands/flags).

### Server
Using the CLI, you can spin up the core as an HTTP server:
- `server start [--host 0.0.0.0] [--port 8000] [--role public|admin|both] [--port-public N] [--port-admin N] [--reload] [--log-level info]`
- `role=public` (default): dynamic routes on `--port`.
- `role=admin`: admin APIs on `--port`.
- `role=both`: runs public on `--port-public` (or `--port`), admin on `--port-admin` (or `--port+1`).

### Routes
From the CLI you can see what routes are available to use.
- `routes list [--show-body] [--full-body] [--decode/--raw]` - list all static + dynamic routes.
- `routes static` - list only static FastAPI routes.
- `routes dynamic [--show-body] [--full-body] [--decode/--raw]` - list DB-backed routes.

### Logs
- `logs tail [--core-url http://127.0.0.1:8000] [--interval 1.0] [--once] [--regex "..."]` - poll `/api/logs` and stream matching entries.

### Forge
- `forge payload --kind xss_basic --endpoint /xss --callback-url http://127.0.0.1:9000/beacon [--method GET] [--status 200] [--content-type text/html] [--dry-run] [--core-url http://127.0.0.1:8001]` - generate a payload and (unless `--dry-run`) create a dynamic route on the admin API to serve it.
- `forge help [kind]` - list available payload kinds or show params/doc for a specific kind (e.g., `forge help xss_basic`).
- Plugins: drop custom generators under `forge_plugins/<family>/<name>.py` (or `~/.reach/forge_plugins/...` or any path in `REACH_FORGE_PLUGIN_PATHS`). Each module exposing `generate(**kwargs)` auto-registers as `<family>_<name>` (e.g., `xss/gh0st.py` → `xss_gh0st`).

### Dev utilities
- `dev reset-db [-y]` - drop and recreate all tables (destroys data).
- `dev clear-logs` - wipe request logs.

## Configuration (env)
This entire project is modular. *(I like to make life hard)*. So the logic for loading values / value priority is as follows: CLI flags > preset > env/.env > defaults ("hardcoded").
- `.env` at repo root is loaded automatically as a fallback; presets and CLI flags can override values from env/.env. Within the .env you can set the following:
  - `REACH_DB_URL` - full SQLAlchemy URL; if set, overrides SQLite.
  - `REACH_DB_FILE` - path to SQLite file (used when no `REACH_DB_URL`).
  - `REACH_DB_ECHO=1` - enable SQLAlchemy echo for debugging.
  - `REACH_FORGE_PLUGIN_PATHS=[]`

### Presets
Presets are "project based" settings and used for quickly spinning up an instance. Not all config (.env) values can be set within the presets
- You can pass a JSON preset to `reach server start` to avoid long flag lists:
  ```json
  {
    "server": {
      "role": "both",
      "public": {"host": "0.0.0.0", "port": 8000},
      "admin": {"host": "0.0.0.0", "port": 8080},
      "reload": false,
      "log_level": "info"
    },
    "db": {
      "url": "sqlite:///./reach_core.db",
      "echo": false
    }
  }
  ```
  Run: `reach server start --preset ./my-preset.json`
  - CLI flags still override the preset when provided (e.g., `--port-public`).

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

## Notes / limitations
- Auth has not been implemented (yet). Protect the admin app (`/api/logs`, `/api/routes`, `/debug/routes`) via network controls or auth; the public app blocks `/api/*` and `/debug/*` but does not enforce auth itself. 
- On a fresh database, run `reach server start` (or call `init_db()`) before `reach routes ...` so the schema exists.
- Dynamic routing currently reserves `/api/*` and `/debug/*`; tighten the reserved prefixes if you need to block docs endpoints (`/docs`, `/openapi.json`, `/redoc`, `/favicon.ico`) on the public app.

## Known issues:
- **reach.logs** does not always show the correct IP address of the asset calling the route. In our testing environment we noticed this when using Cloudflare tunel via docker to expose the public app to the world. 
