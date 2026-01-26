# Servers and protocols

REACH separates public traffic handling from admin control surfaces.

## Public server
The public server serves dynamic routes and protocol handlers.
- HTTP (ASGI)
- FTP (TCP capture)
- WSS (WebSocket)

Start:
```bash
reach server start --role public --host 0.0.0.0 --port 8000
```

## Admin server
The admin server exposes CRUD APIs for routes, rules, logs, and DNS zones.
Start:
```bash
reach server start --role admin --host 127.0.0.1 --port 8001
```

## Combined
Run both public and admin in one process:
```bash
reach server start --role both --port 8000
```

## Protocol selection
The CLI can run multiple public protocol listeners via presets.
See `docs/config.md` for preset examples.
