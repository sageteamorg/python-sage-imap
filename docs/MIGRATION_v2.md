# Migrating to v2.0

## Version

**2.0.0** introduces optional async support. Sync APIs remain on `sage_imap` top-level imports.

## Async API location

- Use **`from sage_imap.aio import AsyncIMAPSession`** (not `sage_imap.asyncio`).
- Install extra: `pip install python-sage-imap[async]`.

## Breaking changes

1. **Version** bumped to `2.0.0` (`sage_imap.__version__`).
2. **Async is opt-in** — not re-exported from `sage_imap.__init__`.
3. **`IMAPTransport`** remains the sync transport; async uses `AsyncIMAPTransport` in `sage_imap.aio`.
4. **OAuth async** — `sage_imap.auth.oauth2_async` uses httpx when `[async]` is installed.

## Non-breaking

- Existing sync code and tests work without `[async]`.
- Shared models, parsers, and `sage_imap.sync.condstore` are unchanged.

## Example mapping

| Sync | Async |
|------|-------|
| `with IMAPSession(...) as s:` | `async with AsyncIMAPSession(...) as s:` |
| `session.connect()` | `await session.connect()` |
| `for msg in session.iter_messages(...):` | `async for msg in session.iter_messages(...):` |
