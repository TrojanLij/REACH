# DNS service

The DNS service is an optional separate REACH tool for OOB callbacks and query logging.  
It is not required for Core runtime, but it integrates with the shared database for zone management and logging.

## Run
```bash
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

## Wildcard vs strict

- Default: wildcard mode (any in-zone name answers A/AAAA)
- `--strict-zone`: only the zone apex answers A/AAAA

## DB-backed zones (recommended)
Zones are stored in the core database and managed via the admin API:

- `GET /api/dns/zones`
- `POST /api/dns/zones`
- `PATCH /api/dns/zones/{id}`
- `DELETE /api/dns/zones/{id}`

The DNS service refreshes zones periodically:

- `--zones-refresh 2.0` (seconds)

## Static zone (optional)
You can still provide a single static zone:
```bash
reach dns serve --domain oob.example.com --a 203.0.113.10
```

## Daemon mode
Run DNS in the background:
```bash
reach dns serve --daemon --pidfile /tmp/reach-dns.pid
```
