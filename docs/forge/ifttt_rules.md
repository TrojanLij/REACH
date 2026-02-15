# Trigger Rules (IFTTT)

Trigger rules in REACH follow an IFTTT model:

- If request matches condition X (or X + Y), then do action Z.

This lets you automate behavior without changing code or restarting services.

## User View

### What a trigger rule does

A trigger rule watches incoming requests and can:

- Return a custom response.
- Save temporary state for later requests.
- Forward request data to another endpoint.
- Create a new dynamic route automatically.

In plain terms:

- "If path is `/login` and query token exists, then respond `200` and store token."

### Rule flow

```text
incoming request
      |
      v
evaluate enabled rules (priority order)
      |
      +--> match: run action (respond / forward / set state / create route)
      |
      +--> no match: continue normal dynamic route behavior
```

### Common examples

Create a simple rule:

```bash
curl -X POST http://127.0.0.1:8001/api/rules \
  -H "Content-Type: application/json" \
  -d '{
    "name": "login-callback",
    "enabled": true,
    "priority": 10,
    "match": {
      "method": "^GET$",
      "path": "^/login$"
    },
    "action": {
      "status_code": 200,
      "content_type": "text/plain",
      "body": "login callback captured"
    }
  }'
```

List rules:

```bash
curl http://127.0.0.1:8001/api/rules
```

Disable a rule:

```bash
curl -X PATCH http://127.0.0.1:8001/api/rules/1 \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

Delete a rule:

```bash
curl -X DELETE http://127.0.0.1:8001/api/rules/1
```

### Useful match fields

- `method`, `path`, `host`, `client_ip`, `body`
- `headers` (map of header -> regex)
- `query` (map of query key -> regex)
- `state_key` and `state` (for multi-step flows)
- `stage` (`pre` or `post`, default `post`)

All match values are regex matches (`re.search`).

### Useful action fields

- Response: `status_code`, `content_type`, `headers`, `body`/`response_body`
- State: `set_state` with `key`, `data`, `ttl_seconds`
- Chaining controls: `chain.max_hops`, `chain.cooldown_seconds`, `chain.ttl_seconds`
- Forwarding: `forward.url`, `forward.method`, `forward.headers`, `forward.body`
- Route creation: `create_route` with method/path/response fields

## Dev

Implementation map:

- Rule API CRUD: `reach.core.api.rules`.
- Rule model/state model: `reach.core.db.models` (`TriggerRule`, `RuleState`).
- Rule engine runtime: `reach.core.routing.dynamic`.
- Template filters: `reach.core.routing.filters`.

Evaluation behavior:

- Rules are evaluated in ascending `priority`, then `id`.
- Default stage is `post` (runs when route exists).
- `match.stage = "pre"` evaluates before route resolution.
- `action.create_route` allows matching and bootstrapping even if route does not exist yet.

Templating behavior:

- Templates use `{{ ... }}`.
- Context includes request fields (`method`, `path`, `headers`, `query`, etc.) and optional `state`.
- Filter syntax uses pipes (`{{query.id|lower}}`).

Minimal full-feature example:

```json
{
  "name": "token-workflow",
  "enabled": true,
  "priority": 5,
  "match": {
    "all": [
      { "method": "^GET$" },
      { "path": "^/callback$" }
    ],
    "state_key": "{{query.token}}",
    "stage": "post"
  },
  "action": {
    "set_state": {
      "key": "{{query.token}}",
      "data": {
        "seen": "yes",
        "ip": "{{client_ip}}"
      },
      "ttl_seconds": 300
    },
    "chain": {
      "max_hops": 3,
      "cooldown_seconds": 5
    },
    "status_code": 200,
    "content_type": "text/plain",
    "body": "ok token={{query.token}}"
  }
}
```
