# Forge Overview

Forge is REACH's generation and execution toolset.

## User View

Forge can run independently, but it is most useful when connected to Core.

- Independent mode: generate content or run workflows without Core-managed route hosting.
- Integrated mode: create content/workflows and connect them to Core-managed routes/logging.

Minimum requirement for operational use:

- Forge must interact with Core (`/api/routes`) if you want live callback endpoints.

### Forge module types

Forge has different module types because they do different jobs:

- Generators create payload content.
- Exploits perform an action or harness other tools to execute a workflow.
- Plugins/packages are the packaging format used to ship generators, exploits, or other Forge extensions.

Quick mental model:

- Use a generator when you need output text/content.
- Use an exploit when you need runtime behavior or tool orchestration.
- Use package/plugin docs when you are creating or maintaining Forge items.

Quick examples:

```bash
reach forge --list
reach forge generator new xss_basic --dry-run --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
reach forge generator new xss_basic --endpoint /xss --core-url http://127.0.0.1:8001 --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
reach forge exploit --list
reach forge exploit run web_local_storage_replay --exploit-kwarg origin=http://127.0.0.1:8000
```

See subpages:

- [Generators](generators.md)
- [Exploits](exploits.md)
- [Plugins and Subpages](plugins.md)
- [Trigger Rules (IFTTT)](ifttt_rules.md)

## Dev

- CLI entry: `reach.cli.forge`
- Generator command: `reach.cli.forge.generator`
- Exploit command: `reach.cli.forge.exploit`
- Core integration client: `reach.core.client`
