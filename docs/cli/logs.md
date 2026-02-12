# `reach logs`

Stream request logs from REACH admin API.

## Tail logs continuously
```bash
reach logs tail --core-url http://127.0.0.1:8001
```

## Fetch once
```bash
reach logs tail --core-url http://127.0.0.1:8001 --once
```

## Filter examples
By protocol:
```bash
reach logs tail --core-url http://127.0.0.1:8001 --protocol dns
```

By DNS label:
```bash
reach logs tail --core-url http://127.0.0.1:8001 --dns-label alice
```

By regex:
```bash
reach logs tail --core-url http://127.0.0.1:8001 --regex "callback|token="
```

Include request headers:
```bash
reach logs tail --core-url http://127.0.0.1:8001 --header
```

