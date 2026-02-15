# FTP Protocol

FTP in REACH is a capture-oriented TCP listener for command logging.
*Note. FTP is still under development and for now is used primarily as a username + password capture interface. If you implement your own version, lets throw it in here. make a pull request and lets test it*

## User View

- REACH accepts FTP client connections and logs FTP command activity.
- Useful for callback/capture scenarios where FTP traffic is expected.
- This is not intended as a full-featured file transfer server.

Common start command:

```bash
reach server start --role public --protocol ftp --host 0.0.0.0 --port 2121
```

## Dev

- Module: `reach.core.protocols.ftp.server`
- Runtime: async TCP server with basic FTP-style responses
- Registration: protocol key `ftp` with `server_type="tcp"`
