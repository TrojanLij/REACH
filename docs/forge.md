# Forge (payload generation)

Forge creates payloads and can register them as dynamic routes via the admin API.

Examples:
```bash
reach forge --list
reach forge payload new xss_basic --endpoint /xss --payload-kwarg callback_url=http://127.0.0.1:9000/beacon
```

Plugins:
- Place custom generators under `forge_plugins/<family>/<name>.py`
- Modules exposing `generate(**kwargs)` are auto-registered
