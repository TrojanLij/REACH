# Logs
REACH persists request logs to the database and exposes them via the admin API.

## Admin API

- `GET /api/logs`
- `GET /api/logs?since_id=<id>&limit=<n>&protocol=<name>`
- `GET /api/logs?protocol=dns&dns_label=<label>` (filter DNS by left-most label)

## CLI
Tail logs from the admin API:
```bash
reach logs tail --core-url http://127.0.0.1:8001
```
Filter DNS logs for a specific operator label:
```bash
reach logs tail --protocol dns --dns-label alice
```

## Notes

- Non-HTTP protocols (FTP/WSS/DNS) log through shared helpers.
- DNS logs include the query type and matched zone (if any).
