# Architecture

REACH is split into distinct runtime surfaces so operators can expose only what is needed.

## Components
- `public server` handles callback traffic and dynamic route responses
- `admin server` exposes management APIs (routes, logs, rules, DNS zones)
- `dns service` provides authoritative OOB callbacks and DNS logging
- `database` stores routes, logs, and zone/rule state

## Data flow
```text
Inbound traffic (HTTP/FTP/WSS/DNS)
        |
        v
Protocol handler -> route/rule resolution -> response
        |
        v
Shared logging -> database -> admin API -> CLI tail/queries
```

## Process layout
- Single-host: run `role=both` + DNS as separate process.
- Multi-host: run public/admin/DNS independently against the same shared DB.

## Why this split matters
- Limits exposure: admin API can stay internal.
- Keeps OOB DNS independent from HTTP listener lifecycle.
- Enables horizontal or host-level separation without changing user workflows.

## Related docs
- `servers.md`
- `dns.md`
- `config.md`
- `logs.md`
