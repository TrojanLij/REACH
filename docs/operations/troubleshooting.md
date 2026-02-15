# Troubleshooting

Quick checks for common setup and runtime issues.

## `reach` command not found
Install the package in your current environment:
```bash
python -m pip install -e .
```

## Logs tail cannot connect to admin API
If running `--role both --port 8000`, admin API is usually on `8001`.
```bash
reach logs tail --core-url http://127.0.0.1:8001
```

## `--reload` fails for server start
Auto-reload is intentionally disabled in current CLI behavior. Remove `--reload`.

## No DNS responses
Check one of these is true:

- `--db-zones` is enabled and zones exist in DB
- or `--domain` is set for static zone mode

If strict mode is on, only apex A/AAAA answers:
```bash
reach dns serve ... --strict-zone
```

## Forge route creation fails
Validate:

- admin URL is reachable (`--core-url`)
- payload kind exists (`reach forge --list`)
- endpoint is provided unless `--dry-run` is used

## Docker server start fails
Validate:

- Docker daemon is running
- image can build from selected `--dockerfile` and `--context`
- required ports are available on host

## DB/state issues during local dev
Dev utilities:

```bash
reach dev clear-logs
reach dev reset-db --yes
```

`reset-db` is destructive and should not be used in shared/prod environments.

