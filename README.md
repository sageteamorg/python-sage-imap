# Python Sage IMAP

[![PyPI version](https://badge.fury.io/py/python-sage-imap.svg)](https://badge.fury.io/py/python-sage-imap)
[![Python](https://img.shields.io/pypi/pyversions/python-sage-imap.svg)](https://pypi.org/project/python-sage-imap/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/sageteamorg/python-sage-imap/graph/badge.svg?token=I10LGK910X)](https://codecov.io/gh/sageteamorg/python-sage-imap)
[![Documentation](https://readthedocs.org/projects/python-sage-imap/badge/?version=latest)](https://python-sage-imap.readthedocs.io/en/latest/)

**Production-oriented IMAP for Python 3.10+** — UID-first mailbox operations, CONDSTORE sync, IDLE, OAuth2, SPECIAL-USE folders, and an optional **async** API (`sage_imap.aio`).

> **Current release:** `2.0.0` — sync API on stdlib `imaplib`; async via optional `[async]` extra (`aioimaplib`).

## Why this library?

Python Sage IMAP targets applications that need reliable email access beyond thin `imaplib` wrappers:

- **UID-first** search, fetch, move, and flag operations via `IMAPMailboxUIDService` and `IMAPSession`
- **Streaming fetch** with `iter_uid_fetch` / `iter_messages` and `ParseMode` (headers-only, minimal, full, raw)
- **Incremental sync** with CONDSTORE (`MailboxSyncState`, `CHANGEDSINCE`)
- **IDLE** for push-style mailbox notifications
- **OAuth2** with refresh (`OAuth2Config`, `ensure_access_token`)
- **Resilience** — retries, connection pooling (`use_pool=True`), metrics, health checks
- **Async parity** — `AsyncIMAPSession` under `sage_imap.aio` (install `[async]`)

## Installation

```bash
pip install python-sage-imap
```

Async support:

```bash
pip install python-sage-imap[async]
```

**Requirements:** Python 3.10+, network access to an IMAP server (TLS recommended).

### Development

```bash
git clone https://github.com/sageteamorg/python-sage-imap.git
cd python-sage-imap
poetry install
poetry install -E async   # optional, for sage_imap.aio tests
poetry run pytest -m "not integration"
```

Integration tests against a Mailcow-compatible stack:

```bash
make integration-up
make integration-test
make integration-down
```

Set `IMAP_HOST`, `IMAP_USER`, `IMAP_PASSWORD`, and optionally `IMAP_PORT`. See [docker/mailcow/README.md](docker/mailcow/README.md).

## Quick start (sync)

Use **`IMAPSession`** as the primary entry point:

```python
from sage_imap import IMAPSession, IMAPSearchCriteria, SpecialUse

with IMAPSession("imap.example.com", "user@example.com", "app-password") as session:
    session.select("INBOX")
    result = session.search(IMAPSearchCriteria.UNSEEN)
    trash = session.special_folder(SpecialUse.TRASH)
    for msg in session.iter_messages(result.to_uid_message_set(), batch_size=50):
        print(msg.uid, msg.subject)
```

More: [docs/SESSION.md](docs/SESSION.md) · [Read the Docs](https://python-sage-imap.readthedocs.io/en/latest/getting_started/imap_session.html)

## Quick start (async)

```python
import asyncio
from sage_imap.aio import AsyncIMAPSession
from sage_imap.helpers.search import IMAPSearchCriteria

async def main():
    async with AsyncIMAPSession("imap.example.com", "user@example.com", "secret") as session:
        await session.select("INBOX")
        result = await session.search(IMAPSearchCriteria.UNSEEN)
        async for msg in session.iter_messages(result.to_uid_message_set()):
            print(msg.subject)

asyncio.run(main())
```

See [docs/ASYNC.md](docs/ASYNC.md) and `examples/09_async_session.py`.

## Sync vs async

| Topic | Sync | Async |
|--------|------|--------|
| Import | `from sage_imap import IMAPSession` | `from sage_imap.aio import AsyncIMAPSession` |
| Transport | `imaplib` + `threading.RLock` | `aioimaplib` + `asyncio.Lock` |
| Install | `pip install python-sage-imap` | `pip install python-sage-imap[async]` |
| OAuth refresh | stdlib (`urllib`) | `httpx` (or thread fallback) |

Async is **not** re-exported from top-level `sage_imap` (by design). See [docs/MIGRATION_v2.md](docs/MIGRATION_v2.md) when upgrading from 1.x.

## Lower-level API

Services remain available for fine-grained control:

```python
from sage_imap import IMAPClient, IMAPMailboxUIDService, IMAPSearchCriteria

with IMAPClient("imap.example.com", "user@example.com", "secret") as client:
    caps = client.transport.get_capabilities()
    mailbox = IMAPMailboxUIDService(client)
    mailbox.select("INBOX")
    result = mailbox.uid_search(IMAPSearchCriteria.ALL)
    for msg in mailbox.iter_uid_fetch(result.to_uid_message_set()):
        print(msg.subject)
```

`IMAPClient` delegates raw `imaplib` methods (e.g. `list`, `select`) when connected; prefer UID services for message operations.

## Examples

Runnable scripts live under [`examples/`](examples/). Configure credentials via environment variables:

```bash
export IMAP_HOST=imap.example.com
export IMAP_USER=user@example.com
export IMAP_PASSWORD=secret
poetry run python examples/01_basic_client_usage.py
```

| Script | Topic |
|--------|--------|
| `01_basic_client_usage.py` | Client, pooling, metrics |
| `02_connection_pooling_example.py` | `use_pool=True` |
| `03_retry_and_resilience_example.py` | Retries and recovery |
| `04_monitoring_and_metrics_example.py` | `ConnectionMetrics` |
| `05_advanced_client_features.py` | OAuth, TLS, health |
| `06_mailbox_operations_example.py` | Mailbox CRUD |
| `07_advanced_mailbox_features.py` | Upload, bulk ops |
| `08_mailbox_uid_operations.py` | UID search/fetch |
| `09_async_session.py` | Async session |

See [examples/README.md](examples/README.md).

## Configuration

```python
from sage_imap import ConnectionConfig, IMAPSession, build_ssl_context

config = ConnectionConfig(
    host="imap.example.com",
    username="user@example.com",
    password="secret",
    port=993,
    use_ssl=True,
    timeout=30.0,
    max_retries=5,
    retry_delay=2.0,
    enable_monitoring=True,
    enable_background_health=False,
)

with IMAPSession.from_config(config) as session:
    session.select("INBOX")
```

## Documentation

- **Online:** https://python-sage-imap.readthedocs.io/
- **Session facade:** [docs/SESSION.md](docs/SESSION.md)
- **Async:** [docs/ASYNC.md](docs/ASYNC.md)
- **v2 migration:** [docs/MIGRATION_v2.md](docs/MIGRATION_v2.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

## Testing

```bash
poetry run pytest -m "not integration"
poetry run pytest tests/aio -m "not integration"   # requires -E async
poetry run pytest --cov=sage_imap --cov-report=html
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

```bash
make setup-dev
make test
make lint
```

## License

MIT — see [LICENSE](LICENSE).

## Support

- [Documentation](https://python-sage-imap.readthedocs.io/)
- [Issues](https://github.com/sageteamorg/python-sage-imap/issues)
- [Discussions](https://github.com/sageteamorg/python-sage-imap/discussions)
