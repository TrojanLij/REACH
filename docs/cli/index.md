# CLI reference

Top-level groups:

- `reach version`
- `reach server ...`
- `reach routes ...`
- `reach logs ...`
- `reach forge ...`
- `reach dns ...`
- `reach dev ...`

Run `--help` on any command for full option details.

## Component relationship

CLI commands can run independently, but most operational commands require Core availability.

- `reach server`, `reach dns`: start runtime services directly.
- `reach forge`, `reach logs`, `reach routes`: typically interact with Core admin/public APIs.

Minimum requirement for meaningful workflow:

- Core must be running (or reachable) for route/log/rule operations.

## Command guides

- `server.md`
- `routes.md`
- `logs.md`
- `forge.md`
- `dns.md`
- `dev.md`

## Version commands
Show REACH package version:
```bash
reach version
```
