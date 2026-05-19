# Examples

Runnable examples for **python-sage-imap** v2. Set credentials with environment variables (same as integration tests):

```bash
export IMAP_HOST=imap.example.com
export IMAP_USER=user@example.com
export IMAP_PASSWORD=your-secret
# optional:
export IMAP_PORT=993
```

Run from the repository root:

```bash
poetry run python examples/01_basic_client_usage.py
```

## Recommended learning path

1. **`01_basic_client_usage.py`** — `IMAPClient`, transport capabilities, metrics
2. **`08_mailbox_uid_operations.py`** — UID search, streaming fetch, `ParseMode`
3. **`06_mailbox_operations_example.py`** — move, copy, append, expunge
4. **`05_advanced_client_features.py`** — OAuth2, TLS, health monitoring
5. **`09_async_session.py`** — async session (requires `pip install python-sage-imap[async]`)

For day-to-day apps, prefer **`IMAPSession`** (sync) or **`AsyncIMAPSession`** (async) instead of wiring services manually. See [docs/SESSION.md](../docs/SESSION.md) and [docs/ASYNC.md](../docs/ASYNC.md).

## Script index

| File | Description |
|------|-------------|
| `01_basic_client_usage.py` | Connection lifecycle, context manager, configuration |
| `02_connection_pooling_example.py` | Global connection pool and `use_pool` |
| `03_retry_and_resilience_example.py` | Retries, backoff, reconnection |
| `04_monitoring_and_metrics_example.py` | Metrics and operation timing |
| `05_advanced_client_features.py` | OAuth, SSL context, background health |
| `06_mailbox_operations_example.py` | Sequence-number mailbox service |
| `07_advanced_mailbox_features.py` | EML upload, bulk processing |
| `08_mailbox_uid_operations.py` | UID mailbox service and CONDSTORE |
| `09_async_session.py` | `AsyncIMAPSession` quick start |

Mailbox-focused notes: [README_mailbox.md](README_mailbox.md).
