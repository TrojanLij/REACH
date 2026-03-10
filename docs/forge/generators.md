# Forge Generators

Generators create payload content.

## User View

### What generators are

A generator produces output you can deliver or embed somewhere else.

- It returns payload content such as script, HTML, XML, or text.
- It can run standalone in dry-run mode.
- It can also register the generated output as a Core route.

In practical terms:

- Generators create the content.
- Core serves the content if you want a live callback endpoint.

### Common workflows

List generator kinds:

```bash
reach forge --list-generators
reach forge generator --list
```

Describe one generator kind:

```bash
reach forge generator --list --kind xss_basic
```

Generate output only:

```bash
reach forge generator new xss_basic \
  --dry-run \
  --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
```

Generate output and register a route in Core:

```bash
reach forge generator new xss_basic \
  --endpoint /xss \
  --core-url http://127.0.0.1:8001 \
  --generator-kwarg callback_url=http://127.0.0.1:8000/beacon
```

Check generator dependencies:

```bash
reach forge generator check --all
reach forge generator check --kind xss_basic
```

Install generator dependencies:

```bash
reach forge generator install --all --upgrade
reach forge generator install --kind xss_basic --dry-run
```

### Built-in and discovered examples

- Built-in example: `src/reach/forge/generators/xss/basic`
- External/discovered examples:
  - `plugins/forge/generators/xss/gh0st`
  - `plugins/forge/generators/xss/zero_width`
  - `plugins/forge/generators/xxe/external_entity`

## Dev

Generator-specific modules:

- CLI: `reach.cli.forge.generator`
- Runtime API: `reach.forge.api`
- Built-in generator registry: `reach.forge.generators`
- Core route registration client path: `reach.core.client`

Entrypoint pattern:

```python
def generate(callback_url: str | None = None, **kwargs) -> str:
    ...
```

Implementation notes:

- Generators return content, not execution result objects.
- The CLI supports both `generator` and backward-compatible `payload` naming.
- When integrated with Core, the generated output is wrapped into a dynamic route response.
