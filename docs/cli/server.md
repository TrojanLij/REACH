# `reach server`

Start and manage REACH Core services.

## Inspect supported protocols
```bash
reach server protocols
```

## Start public server
```bash
reach server start --role public --host 0.0.0.0 --port 8000
```

## Start admin server
```bash
reach server start --role admin --host 127.0.0.1 --port 8001
```

## Start both public and admin
```bash
reach server start --role both --port 8000
```

In `both` mode, admin defaults to `--port + 1` unless overridden.

## Useful options
- `--preset <file>` load JSON config
- `--port-public` and `--port-admin` split listeners explicitly
- `--protocol http|ftp|wss` choose public protocol for single-protocol mode
- `--docker` run through Docker from CLI

For configuration precedence and preset structure, see `../config.md`.
