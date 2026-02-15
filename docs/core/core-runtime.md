# Core Runtime

REACH runtime is split into two surfaces that work together:

- Public interface: handles inbound callback traffic.
- Admin interface: manages runtime state (routes, rules, logs, DNS zones).

Think of it as data-plane vs control-plane:

- Public receives and responds to external traffic.
- Admin changes what public should do next.
- Both persist and read shared state from the same database.

Note:

- DNS is not required for Core runtime.
- DNS runs as an optional separate REACH tool that can still write logs/use DB zones.

## User View

### Public interface

The public side is what targets interact with.

- Serves dynamic routes and payload responses.
- Accepts protocol traffic (HTTP, WSS, FTP listeners).
- Writes request activity into the shared log store.
- Should be reachable from expected callback sources.

### Admin interface

The admin side is for operators only.

- CRUD for routes (`/api/routes`).
- CRUD for trigger rules (`/api/rules`).
- Log access (`/api/logs`).
- DNS zone management (`/api/dns/zones`) for the optional DNS tool.
- Should be private/internal, not internet-exposed.

### How they interact

Admin does not proxy public traffic. Instead, they coordinate through shared persistence:

- Admin writes route/rule/zone configuration into DB.
- Public reads that configuration at request time.
- Public writes request logs into DB.
- Admin (and CLI) read logs from DB through admin APIs.

## Interaction Schema

```text
                 operator / CLI
                       |
                       v
               Admin Interface
      (routes, rules, logs, dns zones APIs)
                       |
                 read / write
                       v
                 Shared Database
             (routes, rules, logs, zones)
                       ^
                 read / write
                       |
               Public Interface
    (HTTP/WSS/FTP request handling + responses)
                       ^
                       |
             internet callback traffic
```

## Runtime Modes

REACH can run these surfaces in different roles:

- `public`: public interface only.
- `admin`: admin interface only.
- `both`: both in one process.

Typical pattern:

- Single host lab: run `both`.
- Production split: run `public` and `admin` separately, sharing one DB.

## Component Independence

REACH components are modular, but they are designed to work together:

- Core can run fully on its own (public/admin runtime).
- CLI can run independently as a toolset, but most commands target Core APIs.
- Forge can generate payloads independently, but route creation requires Core admin API access.
- DNS tool can run independently and still integrate through shared DB/logging.

Minimum operational dependency:

- At least Core must run (or be reachable) for end-to-end callback infrastructure.

## Quick Usage Examples

Start both interfaces in one process:

```bash
reach server start --role both --port 8000
```

This gives you:

- Public listener on `http://127.0.0.1:8000`.
- Admin listener on `http://127.0.0.1:8001` (default `+1` in `both` mode).

Check core health through admin API:

```bash
curl http://127.0.0.1:8001/api/health
```

Stream logs from admin while public receives traffic:

```bash
reach logs tail --core-url http://127.0.0.1:8001
```

Split deployment example:

```bash
# host A (public)
reach server start --role public --host 0.0.0.0 --port 8000

# host B (admin)
reach server start --role admin --host 127.0.0.1 --port 8001
```

## Dev

Implementation map:

- Admin app factory: `reach.core.server` (`create_admin_app`).
- Public HTTP app factory: `reach.core.protocols.http.server` (`create_public_app`).
- Admin route registration: `reach.core.routing.static`.
- Public dynamic routing: `reach.core.routing.dynamic`.
- Shared persistence models: `reach.core.db.models`.

Request-time interaction details:

- Public requests flow through dynamic router and logging middleware.
- Admin APIs mutate route/rule/zone rows directly in DB.
- Public behavior changes immediately as DB-backed state changes.
