# Async IMAP (v2)

Python Sage IMAP provides a first-class async API under **`sage_imap.aio`**, backed by [aioimaplib](https://github.com/bamthoor/aioimaplib).

## Install

```bash
pip install python-sage-imap[async]
```

Core package remains stdlib-only; async adds `aioimaplib` and `httpx` (OAuth refresh).

## Quick start

```python
from sage_imap.aio import AsyncIMAPSession
from sage_imap.helpers.search import IMAPSearchCriteria

async def main():
    async with AsyncIMAPSession("imap.example.com", "user@example.com", "secret") as session:
        await session.select("INBOX")
        result = await session.search(IMAPSearchCriteria.UNSEEN)
        async for msg in session.iter_messages(result.to_uid_message_set()):
            print(msg.subject)

# asyncio.run(main())
```

## Sync vs async

| Concern | Sync | Async |
|---------|------|-------|
| Entry | `sage_imap.IMAPSession` | `sage_imap.aio.AsyncIMAPSession` |
| Transport | `imaplib` + `threading.RLock` | `aioimaplib` + `asyncio.Lock` |
| OAuth refresh | `urllib` (stdlib) | `httpx` or `asyncio.to_thread` fallback |

## One connection per task

A single IMAP connection allows one command stream. Do not share one `AsyncIMAPClient` across concurrent tasks without understanding that all commands are serialized on the transport lock.

## IDLE

```python
from sage_imap.aio.idle import AsyncIMAPIdleSession

async with AsyncIMAPIdleSession(client, "INBOX") as idle:
    result = await idle.wait(timeout=120.0)
    for event in result.events:
        print(event.event_type, event.sequence)
```

See also: [MIGRATION_v2.md](MIGRATION_v2.md), [AIOIMAP_SPIKE.md](AIOIMAP_SPIKE.md).
