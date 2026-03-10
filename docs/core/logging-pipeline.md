# Logging Pipeline

The logging pipeline is how REACH records and exposes callback activity.

- Public protocol handlers write structured request logs.
- Logs are stored in the shared database.
- Operators read logs through the admin API or CLI tail command.

## User View

### What gets logged

REACH captures request data across protocols:

- HTTP requests handled by the public app.
- FTP command traffic.
- WSS connection and message events.
- DNS query events.

Typical log fields include:

- Protocol, method/event, path.
- Status code (when relevant).
- Client IP and host.
- Headers, query params, and body/raw payload data when available.

### How logs flow

```text
inbound protocol traffic
          |
          v
 protocol-specific handler
          |
          v
   structured log write
          |
          v
     shared database
          |
          v
  admin API (/api/logs)
          |
          v
   CLI / scripts
```

### Common usage examples

Start runtime (admin is used for log reads):

```bash
reach server start --role both --port 8000
```

Tail logs continuously:

```bash
reach logs tail --core-url http://127.0.0.1:8001
```

Fetch once:

```bash
reach logs tail --core-url http://127.0.0.1:8001 --once
```

Filter by protocol:

```bash
reach logs tail --core-url http://127.0.0.1:8001 --protocol dns
```

Filter DNS by label:

```bash
reach logs tail --core-url http://127.0.0.1:8001 --dns-label alice
```

Filter with regex:

```bash
reach logs tail --core-url http://127.0.0.1:8001 --regex "token=|callback"
```

Include request headers in output:

```bash
reach logs tail --core-url http://127.0.0.1:8001 --header
```

### API examples

Get recent log entries:

```bash
curl "http://127.0.0.1:8001/api/logs?since_id=0&limit=50"
```

Incremental polling from last seen id:

```bash
curl "http://127.0.0.1:8001/api/logs?since_id=1250&limit=200"
```

Only DNS logs for a label:

```bash
curl "http://127.0.0.1:8001/api/logs?protocol=dns&dns_label=alice"
```

### Practical note

Use the admin URL (`:8001` in typical `both` mode) for log reads.  
If you query the public interface by mistake, `/api/logs` will not be available there.

## Dev

Implementation map:

- DB-backed logging service: `reach.core.logging`.
- Logs API endpoint: `reach.core.api.logs`.
- Shared protocol logging helper: `reach.core.protocols.logging`.
- HTTP logging path: `reach.core.routing.dynamic`.
- DNS logging path: `reach.dns.server`.
- Log table schema: `reach.core.db.models` (`RequestLog`).

Behavior details:

- HTTP dynamic handler logs rich request context and avoids double-logging via request state.
- Non-HTTP protocols call `log_protocol_request(...)` to keep field shape consistent.
- Log reads use incremental cursor style (`since_id`) for tailing/polling clients.
- DNS label filter is resolved in API layer by parsing DNS log fields (`zone` + qname prefix).

Operational notes:

- Logs are persistent DB records, not in-memory-only session data.
- `reach dev clear-logs` clears the `request_logs` table (destructive for history).
