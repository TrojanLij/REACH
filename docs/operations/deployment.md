# Deployment

Use the smallest deployment shape that fits your engagement.

## 1. Local single-host (recommended for development)
```bash
reach server start --role both --port 8000
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

Good for feature testing and low-friction local demos.

## 2. Multi-host (recommended for team/engagement use)
All services point to the same DB:
```bash
REACH_DB_URL=postgresql://user:pass@DB_IP:5432/reach
```

Example split:

- admin host: `reach server start --role admin --host ADMIN_IP --port 8001`
- public host: `reach server start --role public --host PUBLIC_IP --port 8000`
- dns host: `reach dns serve --host DNS_IP --port 53 --db-zones`

This setup improves isolation and allows separate network controls.

## 3. Dockerized backend-only stack (recommended for local operator devices)

This shape runs REACH Core (public + admin) in one container, with persistent
SQLite state and local plugin/preset mounts.

Start:
```bash
docker compose up -d --build
```

Validate:
```bash
curl -s http://127.0.0.1:8001/api/health
```

Stop:
```bash
docker compose down
```

Notes:

- DNS is also out of scope here; run it separately only if needed.
- DB state is persisted in the Docker volume `reach_data`.
- `./plugins` is mounted read-only so local plugin edits are available immediately.

Cloudflare Tunnel pattern (public HTTP listener on `:8000`):
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

## 4. Dockerized core server via CLI
The server command can also launch Docker directly:
```bash
reach server start --role both --docker --image reach:local
```

Common flags:

- `--rebuild` rebuild image before run
- `--name` set container name
- `--dockerfile` choose Dockerfile path
- `--context` choose build context
- `--detach/--no-detach` run background or foreground

## Security baseline

- Bind admin to private interfaces only.
- Use strict firewall rules around DNS and admin ports.
- Use short-lived infrastructure and engagement-specific domains.
- Keep explicit authorization artifacts for every deployment.

## Related docs

- [Configuration](config.md)
- [Persistence Layer](../core/persistence-layer.md)
- [Security Boundaries](../core/security-boundaries.md)
- [Servers and Protocols](servers.md)
- [DNS Service](dns.md)
