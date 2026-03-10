# Basic XSS (Built-in Forge Generator)

Generates a simple reflected XSS payload.

- Without `callback_url`: `alert('xss')`
- With `callback_url`: sends cookie beacon via `fetch`
