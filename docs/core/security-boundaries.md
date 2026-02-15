# Security Boundaries

REACH separates external callback handling from operator control APIs.  
This split is the main security boundary and should be enforced in deployment.

## User View

### Core boundary model

- Public interface: intentionally exposed for callback traffic.
- Admin interface: control plane, should stay private/internal.
- DNS service: external-facing only where needed for OOB callbacks.

### High-level exposure rules

- Expose public listeners only as required by engagement scope.
- Do not expose admin API directly to the internet.
- Restrict DNS listener to required networks and ports.

### Reserved paths protection

Public routing rejects reserved admin/docs/debug prefixes so callback paths cannot override control endpoints.

### HTTPS / TLS reality

Native HTTPS termination is not yet implemented directly in REACH core.

Recommended pattern:

- Terminate TLS at Cloudflare Tunnel or an edge proxy/load balancer.
- Forward HTTP to REACH public listener on internal/local network.

Cloudflare Tunnel quick example:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Nginx quick pattern:

```nginx
location / {
  proxy_pass http://127.0.0.1:8000;
}
```

### Operator hardening checklist

- Bind admin to `127.0.0.1` or private interface.
- Put admin behind VPN/internal network and firewall allowlist.
- Keep engagement-specific infrastructure short-lived.
- Use Postgres + network controls for shared/team deployments.
- Monitor logs for unexpected access patterns.
- Treat `reach dev reset-db --yes` as destructive and restricted.

## Dev

Implementation map:

- Admin app surface: `reach.core.server` (`create_admin_app`).
- Public app surface: `reach.core.protocols.http.server` (`create_public_app`).
- Reserved path checks: `reach.core.routing.reserved`.
- Dynamic public router: `reach.core.routing.dynamic`.
- DNS server runtime: `reach.dns.server`.

Current constraints and notes:

- No built-in auth layer is applied to admin API routes by default.
- Admin/public CORS middleware is permissive by default; rely on network boundary and edge controls.
- Public OpenAPI/docs are disabled; admin docs are available on admin surface.
- CLI token option exists but is not active auth enforcement for admin APIs today.
