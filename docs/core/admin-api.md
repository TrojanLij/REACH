# Admin API Surface

The admin API is REACH's control interface.

- It is where operators manage runtime behavior.
- It is separate from public callback traffic.
- It should stay internal and access-controlled.

## User View

### What this API is for

Use the admin API when you want to:

- Create or update callback routes.
- Review captured logs.
- Define trigger rules.
- Manage DNS zones used by the DNS service.

In simple terms:

- Public interface handles target traffic.
- Admin API tells public interface what to do.

### Main endpoint groups

- `/api/health` for status checks.
- `/api/routes` for dynamic route management.
- `/api/logs` for log retrieval and tailing.
- `/api/rules` for trigger rule management.
- `/api/dns/zones` for DNS zone management.

### Interaction schema

```text
operator tools (CLI / curl / scripts)
              |
              v
          Admin API
   (/api/routes, /api/logs, ...)
              |
        read / write state
              v
         Shared database
              ^
              |
    Public interface uses this data
      while handling live traffic
```

### Common usage examples

Start combined runtime:

```bash
reach server start --role both --port 8000
```

Check admin health:

```bash
curl http://127.0.0.1:8001/api/health
```

List routes:

```bash
curl http://127.0.0.1:8001/api/routes
```

Create a route:

```bash
curl -X POST http://127.0.0.1:8001/api/routes \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/hello",
    "status_code": 200,
    "response_body": "hello from REACH",
    "content_type": "text/plain",
    "headers": {}
  }'
```

Tail logs from CLI:

```bash
reach logs tail --core-url http://127.0.0.1:8001
```

Read logs through API:

```bash
curl "http://127.0.0.1:8001/api/logs?since_id=0&limit=20"
```

Create a trigger rule:

```bash
curl -X POST http://127.0.0.1:8001/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "match-login-path",
    "enabled": true,
    "priority": 100,
    "match": {"path": "^/login$"},
    "action": {"type": "response", "status_code": 200, "body": "ok"}
  }'
```

List DNS zones:

```bash
curl http://127.0.0.1:8001/api/dns/zones
```

Create a DNS zone:

```bash
curl -X POST http://127.0.0.1:8001/api/dns/zones \
  -H "Content-Type: application/json" \
  -d '{
    "zone": "oob.example.test",
    "a": "203.0.113.10",
    "ttl": 60,
    "wildcard": true,
    "enabled": true
  }'
```

## Dev

Implementation map:

- Admin app factory: `reach.core.server`.
- Admin route registration: `reach.core.routing.static`.
- API routers:
  - `reach.core.api.routes`
  - `reach.core.api.logs`
  - `reach.core.api.rules`
  - `reach.core.api.dns_zones`
- Request/response schemas: `reach.core.db.schemas`.

Design notes:

- APIs are mounted only on the admin interface, not public listeners.
- CRUD writes are persisted in shared DB tables (`routes`, `trigger_rules`, `dns_zones`).
- Public runtime behavior is DB-driven, so API updates are reflected without redeploy.
- Log retrieval supports incremental polling (`since_id`) for tail-style clients.

Operational notes:

- Keep admin bind private (for example `127.0.0.1` or internal network).
- Place auth/reverse proxy controls in front of admin endpoints when exposed beyond local host.
