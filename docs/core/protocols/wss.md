# WSS Protocol

WSS support lets REACH handle WebSocket callback routes.
*Note. WSS is still under development. If you implement your own version, lets throw it in here. make a pull request and lets test it*


## User View

- WebSocket route matching uses DB route path entries.
- If a route exists, REACH accepts connection and logs events/messages.
- If no route exists, REACH closes the connection.

Common start command:

```bash
reach server start --role public --protocol wss --host 0.0.0.0 --port 8000
```

## Dev

- Module: `reach.core.protocols.wss.server`
- App factory: `create_public_app()`
- Registration: protocol key `wss` via `register_protocol(...)`
