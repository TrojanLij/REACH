# Forge Generator Workflows

This page covers common Forge usage patterns.

## User View

List available generator kinds:

```bash
reach forge --list
```

Create a generated route (writes to Core admin API):

```bash
reach forge generator new xss_basic \
  --endpoint /xss \
  --generator-kwarg callback_url=http://127.0.0.1:8000/beacon \
  --core-url http://127.0.0.1:8001
```

Generate only (no route creation):

```bash
reach forge generator new xss_basic --dry-run \
  --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
```

## Dev

- CLI module: `reach.cli.forge.generator`
- Core API client: `reach.core.client`
- Controller workflow: `reach.forge.api`
