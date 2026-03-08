# External Entity XXE (Forge Generator)

Generates a minimal XXE payload that references an external callback URL.

## Usage

```bash
reach forge generator new xxe_external_entity \
  --dry-run \
  --generator-kwarg callback_url=https://callback.local/xxe
```
