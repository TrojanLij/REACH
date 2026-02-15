# Forge Payload Workflows

This page covers common Forge usage patterns.

## User View

List available payload kinds:

```bash
reach forge --list
```

Create a payload route (writes to Core admin API):

```bash
reach forge payload new xss_basic \
  --endpoint /xss \
  --payload-kwarg callback_url=http://127.0.0.1:8000/beacon \
  --core-url http://127.0.0.1:8001
```

Generate only (no route creation):

```bash
reach forge payload new xss_basic --dry-run \
  --payload-kwarg callback_url=http://127.0.0.1:8000/beacon
```

## Dev

- CLI module: `reach.cli.forge.payload`
- Core API client: `reach.core.client`
- Controller workflow: `reach.forge.api`
