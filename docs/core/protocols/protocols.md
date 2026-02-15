# Protocols Architecture

REACH supports multiple callback protocols and sends their events into one shared logging system.

## User View

### Supported protocols

Core public protocol handlers:

- HTTP (public callback routes)
- WSS (WebSocket routes)
- FTP (command capture listener)

Optional separate REACH tool:

- DNS service (authoritative OOB DNS process with DB/log integration)

See protocol-specific pages:

- [HTTP](http.md)
- [FTP](ftp.md)
- [WSS](wss.md)

### How protocols fit together

```text
internet traffic (http / wss / ftp / dns)
                 |
                 v
          protocol handlers
                 |
                 v
     dynamic routing + logging pipeline
                 |
                 v
            shared database
                 |
                 v
         admin API + operator CLI
```

### HTTPS/TLS status

Direct HTTPS termination is not yet implemented natively in REACH core (currently tracked for future work/TODO).

Current operator pattern:

- Terminate TLS at an edge layer.
- Forward plain HTTP to REACH public listener (usually `127.0.0.1:8000` or internal network port).

### Practical TLS workarounds

Cloudflare Tunnel example:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Nginx reverse proxy example:

```nginx
server {
  listen 443 ssl;
  server_name callbacks.example.com;

  ssl_certificate     /etc/letsencrypt/live/callbacks.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/callbacks.example.com/privkey.pem;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
  }
}
```

You can apply the same pattern with other L7 proxies/load balancers.

### Operator commands

List supported public protocols:

```bash
reach server protocols
```

Run public HTTP listener:

```bash
reach server start --role public --protocol http --host 0.0.0.0 --port 8000
```

Run public WSS listener:

```bash
reach server start --role public --protocol wss --host 0.0.0.0 --port 8000
```

Run public FTP listener:

```bash
reach server start --role public --protocol ftp --host 0.0.0.0 --port 2121
```

Run optional DNS service:

```bash
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

## Dev

Implementation map:

- Protocol registry: `reach.core.protocols.registry`.
- HTTP protocol app: `reach.core.protocols.http.server`.
- WSS protocol app: `reach.core.protocols.wss.server`.
- FTP protocol server: `reach.core.protocols.ftp.server`.
- Shared protocol log helper: `reach.core.protocols.logging`.
- DNS add-on runtime: `reach.dns.server`.

Behavior notes:

- Protocol modules self-register via `register_protocol(...)`.
- `server_type` distinguishes ASGI protocols (`http`, `wss`) from TCP protocol handlers (`ftp`).
- Protocol events are normalized and persisted through shared log writing.
- DNS is intentionally separate from core public/admin app lifecycle and is not required.

### Add or remove protocols

REACH protocols are registry-driven.

To add a protocol:

- Implement a protocol runtime module under `reach.core.protocols.<name>`.
- Register it with `reach.core.protocols.registry.register_protocol(...)`.
- Ensure logging flows through `reach.core.protocols.logging.log_protocol_request(...)` when applicable.
- Add docs pages and nav entries for the new protocol.

To remove a protocol:

- Remove its registration call or stop importing its module.
- Remove CLI/docs references so users do not see unavailable protocol options.
- Keep backward-compatibility notes if operators already use presets with that protocol key.
