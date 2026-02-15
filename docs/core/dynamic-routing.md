# Dynamic Routing

Dynamic routing is how REACH serves callback endpoints without changing code.

- You create routes at runtime through the admin API or CLI.
- REACH stores them in the database.
- The public interface serves responses when matching traffic arrives.

## User View

### What it means in plain terms

Think of a dynamic route as a rule:

- If request method and path match, return this response.
- If nothing matches, return `404`.

Each route defines:

- HTTP method (`GET`, `POST`, etc.).
- Path (for example `/beacon`).
- Status code (for example `200`).
- Response body (text or base64-encoded bytes).
- Content type and optional response headers.

### Request Flow

```text
inbound request
    |
    v
match method + path in DB
    |
    +--> match found: return stored response
    |
    +--> no match: return 404
    |
    v
write request log entry
```

### Common usage examples

Start REACH in combined mode:

```bash
reach server start --role both --port 8000
```

Create a route with Forge:

```bash
reach forge payload new xss_basic \
  --endpoint /beacon \
  --payload-kwarg callback_url=http://127.0.0.1:8000/ping \
  --core-url http://127.0.0.1:8001
```

Trigger the route:

```bash
curl -i http://127.0.0.1:8000/beacon
```

Inspect dynamic routes:

```bash
reach routes dynamic --show-body
```

Watch incoming requests:

```bash
reach logs tail --core-url http://127.0.0.1:8001
```

### Admin API examples

List stored routes:

```bash
curl http://127.0.0.1:8001/api/routes
```

Create a route directly:

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

## Dev

Implementation map:

- Catch-all dynamic handler: `reach.core.routing.dynamic`.
- Path guard for reserved routes: `reach.core.routing.reserved`.
- Route CRUD API: `reach.core.api.routes`.
- Route persistence model: `reach.core.db.models` (`Route`).

Request lifecycle details:

- Middleware logs all requests not already logged by the dynamic handler.
- Dynamic handler reads body, context, and query/header data.
- Route lookup uses exact `method + path` match against DB.
- If a matching trigger rule exists, rule action is applied before response.
- Response body supports plain text (`none`) and base64-decoded bytes (`base64`).

Developer notes:

- Stored paths are normalized without leading slash in DB.
- User-facing APIs accept `/path` and normalize internally.
- Reserved admin/debug/doc paths are blocked from dynamic handling.
