# Forge Overview

Forge is REACH's payload-generation component.

## User View

Forge can run independently as a payload generator, but it is most useful when connected to Core.

- Independent mode: generate payloads only.
- Integrated mode: generate payloads and register callback routes via Core admin API.

Minimum requirement for operational use:

- Forge must interact with Core (`/api/routes`) if you want live callback endpoints.

Quick examples:

```bash
reach forge --list
reach forge payload new xss_basic --dry-run --payload-kwarg callback_url=http://127.0.0.1:8000/beacon
reach forge payload new xss_basic --endpoint /xss --core-url http://127.0.0.1:8001 --payload-kwarg callback_url=http://127.0.0.1:8000/beacon
```

See subpages:

- [Payload Workflows](payloads.md)
- [Plugins and Subpages](plugins.md)
- [Trigger Rules (IFTTT)](ifttt_rules.md)

## Dev

- CLI entry: `reach.cli.forge`
- Payload command: `reach.cli.forge.payload`
- Core integration client: `reach.core.client`
