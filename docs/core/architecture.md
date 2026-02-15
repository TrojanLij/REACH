# Architecture

REACH is split into distinct runtime surfaces so operators can expose only what is needed.

## Components

- `public server` handles callback traffic and dynamic route responses
- `admin server` exposes management APIs (routes, logs, rules, DNS zones)
- `database` stores routes, logs, and zone/rule state
- `dns service` is an optional add-on tool for OOB callbacks and DNS logging

## Data flow
```text
Inbound traffic (HTTP/FTP/WSS)
        |
        v
Protocol handler -> route/rule resolution -> response
        |
        v
Shared logging -> database -> admin API -> CLI tail/queries

Optional DNS add-on:
DNS query -> DNS service -> shared logging/database -> admin API/CLI
```

## Process layout

- Single-host: run `role=both`; add DNS as separate process only when needed.
- Multi-host: run public/admin independently; run DNS separately only for OOB DNS use-cases.

## Why this split matters

- Limits exposure: admin API can stay internal.
- Keeps optional OOB DNS independent from core HTTP listener lifecycle.
- Enables horizontal or host-level separation without changing user workflows.

## Related docs

- [Servers and Protocols](../operations/servers.md)
- [DNS Service](../operations/dns.md)
- [Configuration](../operations/config.md)
- [Logs](../operations/logs.md)
- [Persistence Layer](persistence-layer.md)
- [Security Boundaries](security-boundaries.md)
