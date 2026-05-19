# Mailcow / IMAP integration test stack

## Quick start (lightweight Dovecot)

```bash
docker compose -f docker/mailcow/docker-compose.yml up -d
./scripts/wait-for-imap.sh
export IMAP_HOST=127.0.0.1
export IMAP_PORT=993
export IMAP_USER=imaptest@test.local
export IMAP_PASSWORD=testpassword
export IMAP_USE_SSL=true
poetry run pytest -m integration
```

## Full Mailcow

For production-parity testing against [mailcow-dockerized](https://github.com/mailcow/mailcow-dockerized), clone that repository alongside this project and follow their install guide. Point integration tests at your Mailcow host using the same environment variables.

## Teardown

```bash
docker compose -f docker/mailcow/docker-compose.yml down
```
