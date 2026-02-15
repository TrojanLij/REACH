# `reach forge`

Generate payloads and register routes through the admin API.

## List payload kinds
```bash
reach forge --list
```

Describe one kind:
```bash
reach forge --list --kind xss_basic
```

## Generate payload and create route
```bash
reach forge payload new xss_basic \
  --endpoint /xss \
  --payload-kwarg callback_url=http://127.0.0.1:8000/beacon \
  --core-url http://127.0.0.1:8001
```

## Dry run (no route creation)
```bash
reach forge payload new xss_basic \
  --dry-run \
  --payload-kwarg callback_url=http://127.0.0.1:8000/beacon
```

## Useful options

- `--header KEY=VALUE` set response headers (repeatable)
- `--server-header-file <path>` pick `Server` header values from file
- `--method`, `--status`, `--content-type` tune route response metadata

See `../forge/forge.md` for plugin-level behavior.
