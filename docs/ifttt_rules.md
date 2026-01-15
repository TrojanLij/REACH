# IFTTT Rules

This document describes the IFTTT rule system, how rules are evaluated, and the supported match/action parameters.

## Evaluation model

- Rules are evaluated in priority order (lowest `priority` first, then lowest `id`).
- Default behavior is **post-route**: the rule only applies if a dynamic route exists.
- Rules can explicitly set `match.stage: "pre"` to run before route lookup.
- If a rule has `action.create_route`, it can still match without an existing route and will create the route for future requests.

## Rule object

Each rule is a JSON object with:
- `name` (string)
- `enabled` (bool, default: true)
- `priority` (int, default: 100)
- `match` (object)
- `action` (object)

## Match parameters

All match values are regexes (Python `re.search`). Use `^...$` for exact matches.

Leaf fields:
- `method` (string) - HTTP method (`GET`, `POST`, etc.)
- `path` (string) - request path, e.g. `/callback`
- `host` (string)
- `client_ip` (string)
- `body` (string) - request body as text
- `headers` (object) - map of header name -> regex, header names are case-insensitive
- `query` (object) - map of query param -> regex
- `state_key` (string, template) - resolves to a state key, used with `state`
- `state` (object) - map of state field -> regex
- `stage` (string) - `pre` or `post` (default: `post`)

Boolean composition:
- `all` (list of match blocks)
- `any` (list of match blocks)
- `not` (match block or list)

## Action parameters

Response:
- `status_code` (int)
- `content_type` (string)
- `headers` (object)
- `body` or `response_body` (string)

State:
- `set_state` (object)
  - `key` (string, template)
  - `data` (object, templated values)
  - `ttl_seconds` (int, optional)

Chaining:
- `chain` (object)
  - `max_hops` (int, optional)
  - `cooldown_seconds` (int, optional)
  - `ttl_seconds` (int, optional)

Forwarding (server side request, not user side, to redirect / forward the user, use "Location"):
- `forward` (object)
  - `url` (string, template)
  - `method` (string, default: `POST`)
  - `headers` (object, templated values)
  - `body` (string, template)
  - `timeout_seconds` (int/float, default: 5)

Create route:
- `create_route` (object)
  - `method` (string, default: current request method)
  - `path` (string, default: current request path)
  - `status_code` (int, default: 200)
  - `content_type` (string, default: `text/plain`)
  - `response_body` (string, default: `OK`)
  - `body_encoding` (string, default: `none`)
  - `headers` (object)

## Templates and filters

Templates use `{{ ... }}` and can reference request context:
- `method`, `path`, `host`, `client_ip`, `body`
- `headers.<name>`
- `query.<param>`
- `state.<field>`

Filters are appended with `|`:
- `lower`, `upper`, `strip`
- `b64encode`, `b64decode`
- `url_encode`, `url_decode`
- `json`

Custom filters can be loaded from:
- `./plugins/rule_filters/*.py`
- `~/.reach/plugins/rule_filters/*.py`
- `REACH_RULE_FILTER_PATHS`

## Example

```json
{
  "name": "callback-rule",
  "priority": 10,
  "match": {
    "path": "/callback",
    "method": "GET",
    "stage": "post",
    "state_key": "{{query.token}}",
    "state": { "confirmed": "^yes$" }
  },
  "action": {
    "chain": { "max_hops": 3, "cooldown_seconds": 5 },
    "set_state": {
      "key": "{{query.token}}",
      "data": { "confirmed": "yes" }
    },
    "forward": {
      "url": "http://127.0.0.1:9000/ingest",
      "method": "POST",
      "headers": { "content-type": "text/plain" },
      "body": "token={{query.token}}"
    },
    "create_route": {
      "method": "GET",
      "path": "/callback",
      "response_body": "OK"
    },
    "status_code": 200,
    "body": "rule handled"
  }
}
```
