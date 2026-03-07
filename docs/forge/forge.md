# Forge Overview

Forge is REACH's generator and exploit component.

## User View

Forge can run independently as a generator module, but it is most useful when connected to Core.

- Independent mode: generate output only.
- Integrated mode: generate output and register callback routes via Core admin API.

Minimum requirement for operational use:

- Forge must interact with Core (`/api/routes`) if you want live callback endpoints.

Quick examples:

```bash
reach forge --list
reach forge generator new xss_basic --dry-run --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
reach forge generator new xss_basic --endpoint /xss --core-url http://127.0.0.1:8001 --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
```

See subpages:

- [Generators](generators.md)
- [Plugins and Subpages](plugins.md)
- [Trigger Rules (IFTTT)](ifttt_rules.md)

## Dev

- CLI entry: `reach.cli.forge`
- Generator command: `reach.cli.forge.generator`
- Core integration client: `reach.core.client`
