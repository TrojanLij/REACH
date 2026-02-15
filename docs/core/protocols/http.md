# HTTP Protocol

HTTP is the primary public callback protocol in REACH.

## User View

- Dynamic routes are matched by `method + path`.
- Route responses come from DB-stored route definitions.
- If no dynamic route matches, REACH returns `404`.

Common start command:

```bash
reach server start --role public --protocol http --host 0.0.0.0 --port 8000
```

## Dev

- Module: `reach.core.protocols.http.server`
- App factory: `create_public_app()`
- Registration: protocol key `http` via `register_protocol(...)`
