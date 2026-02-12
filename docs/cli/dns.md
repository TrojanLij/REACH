# `reach dns`

Run DNS service for OOB callbacks and query logging.

## Start with DB-backed zones
```bash
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

## Start with static single zone
```bash
reach dns serve --domain oob.example.com --a 203.0.113.10
```

## Useful options
- `--strict-zone` disable wildcard subdomain answering
- `--zones-refresh 2.0` DB zone refresh interval in seconds
- `--tcp` also listen on TCP
- `--daemon --pidfile /tmp/reach-dns.pid` run background service (POSIX)
- `--async-logging` reduce response blocking under heavy query load

For zone CRUD APIs and behavior details, see `../dns.md`.
