# `reach routes`

Inspect static and dynamic routes.

## List all routes
```bash
reach routes list
```

## List only static framework routes
```bash
reach routes static
```

## List only dynamic DB-backed routes
```bash
reach routes dynamic
```

## Show payload bodies
```bash
reach routes dynamic --show-body
reach routes dynamic --full-body
```

Dynamic route commands support `--decode/--raw` for base64 payload display.

