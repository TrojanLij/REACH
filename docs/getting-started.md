# Getting started

This guide gets you from clone to first callback capture quickly.

## Prerequisites
- Python 3.12+
- Local terminal with network access to your chosen ports

## Install
```bash
python -m pip install -e .
```

## Start core services
Run public and admin together:
```bash
reach server start --role both --port 8000
```

With `--role both`, public traffic is served on `8000` and admin API defaults to `8001`.

## Create a test payload route
In a second terminal:
```bash
reach forge payload new xss_basic \
  --endpoint /xss \
  --payload-kwarg callback_url=http://127.0.0.1:8000/beacon \
  --core-url http://127.0.0.1:8001
```

## Observe requests
In a third terminal:
```bash
reach logs tail --core-url http://127.0.0.1:8001
```

Request your route:
```bash
curl -i http://127.0.0.1:8000/xss
```

You should see a new log entry in the tail output.

## Optional: start DNS for OOB
```bash
reach dns serve --host 0.0.0.0 --port 53 --db-zones
```

## Next steps
- Read `architecture.md` for system behavior and boundaries.
- Read `cli/index.md` for command-level details.
- Read `deployment.md` before exposing REACH outside local development.
