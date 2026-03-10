# `reach forge`

Generate exploit output and register routes through the admin API.

## List kinds
```bash
reach forge --list
```

Describe one kind:
```bash
reach forge --list --kind xss_basic
```

List only generator kinds:
```bash
reach forge --list-generators
```

List only exploit kinds:
```bash
reach forge --list-exploits
```

Exploit-scoped listing:
```bash
reach forge exploit --list
reach forge exploit --list --kind web_local_storage_replay
```

## Generate output and create route
```bash
reach forge generator new xss_basic \
  --endpoint /xss \
  --generator-kwarg callback_url=http://127.0.0.1:8000/beacon \
  --core-url http://127.0.0.1:8001
```

## Dry run (no route creation)
```bash
reach forge generator new xss_basic \
  --dry-run \
  --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
```

## Useful options

- `--header KEY=VALUE` set response headers (repeatable)
- `--server-header-file <path>` pick `Server` header values from file
- `--method`, `--status`, `--content-type` tune route response metadata

## Dependency check and install

```bash
reach forge exploit check --kind web_local_storage_replay
reach forge exploit install --kind web_local_storage_replay --dry-run

reach forge generator check --all
reach forge generator install --all --upgrade
```

## Plugin package lifecycle

Scaffold a new minimal package:

```bash
reach forge scaffold generator demo_payload --id demo.payload --category demo
```

Validate packages:

```bash
reach forge validate --root plugins/forge
reach forge validate --root src/reach/forge
```

Reorganize package folders:

```bash
reach forge cleanup --source-root forge --destination-root plugins/forge --dry-run
reach forge cleanup --source-root forge --destination-root plugins/forge --apply
```

See related Forge docs:

- [Forge Overview](../forge/forge.md)
- [Generators](../forge/generators.md)
- [Exploits](../forge/exploits.md)
- [Plugins and Subpages](../forge/plugins.md)
