# namecheap_ddns

Configure your Namecheap credentials in `.env`, then build and start:

```sh
docker compose up -d --build
```

Logs are written to `./logs/current.log` on the host through a bind mount at
`/logs` in the container. Compose creates the host directory if it is missing;
it must be writable by the container. Logs also appear in `docker logs`.

Both outputs use JSON Lines (one JSON object per log entry), for example:

```json
{"timestamp":"2026-11-12T13:45:00+00:00","level":"INFO","message":"DNS IP address updated","action":"update_ip","status":"success","domain":"example.com","subdomain":"home","ip":"203.0.113.10"}
```

Failed updates include `error` or `http_status` fields as appropriate.
Public IP lookup failures use `action: "get_public_ip"` and `service_url`.
Timestamps are UTC. Existing plain-text entries remain until rotation;
new entries use JSON.

The active file rotates daily at midnight UTC, on the next log message.
Archives are gzip-compressed as `current.log.YYYY-MM-DD.gz`, with the date
identifying the log period. By default, the 14 most recent daily archives are retained and older
archives are removed during rotation. These are single compressed log files,
so they use `.gz` rather than `.tgz` (a compressed tar archive).

Set `LOG_RETENTION_DAYS=30` in `.env` to keep 30 daily archives instead.
The value must be a positive integer; the default is `14`. Retention counts
daily archives, so days without log messages do not count toward this limit.
Rebuild and recreate the container with `docker compose up -d --build` after changes.

Change `./logs` in `docker-compose.yml` to use another host directory. When
running the Python script outside Docker, set `LOG_DIR` to a writable directory
(for example, `LOG_DIR=./logs python3 namecheap_ddns.py`).
