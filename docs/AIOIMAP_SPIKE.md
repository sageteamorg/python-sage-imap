# aioimaplib spike — API mapping

Validated against **aioimaplib 1.2.0** (Poetry extra `[async]`).

## Connection lifecycle

| Sync (`imaplib`) | Async (`aioimaplib`) |
|------------------|----------------------|
| `IMAP4_SSL(host, port, ssl_context=ctx)` | `IMAP4_SSL(host, port, ssl_context=ctx, timeout=…)` |
| implicit greeting | `await wait_hello_from_server()` |
| `login(user, password)` | `await login(user, password)` → `Response` |
| XOAUTH2 via `authenticate` | `await xoauth2(user, token)` |
| `logout()` | `await logout()` |

## Response shape

aioimaplib returns `Response(result: str, lines: list[bytes])`.  
`AsyncIMAPTransport` normalizes to sync `IMAPResponse = tuple[str, list[Any]]` via `sage_imap.aio._response`.

## Mailbox commands

| Sync | Async |
|------|-------|
| `select(mailbox)` | `await select(mailbox)` |
| `close()` | `await close()` |
| `status(mailbox, names)` | `await status(mailbox, names)` |
| `uid("SEARCH", charset, criteria)` | `await uid_search(criteria, charset=…)` |
| `uid("FETCH", set, parts)` | `await fetch(set, parts, by_uid=True)` via `protocol.fetch` |
| `uid("STORE", …)` | `await store(…, by_uid=True)` or `await uid("STORE", …)` |
| `uid("COPY"/"MOVE", …)` | `await copy` / `await move` with `by_uid=True` |

## IDLE

| Sync (`IMAPTransport`) | Async |
|------------------------|-------|
| `idle_start()` | `await idle_start()` (returns Future) |
| `idle_done()` | `idle_done()` |
| `idle_read_lines(timeout)` | `await wait_server_push(timeout)` + parse lines |

## Capability gaps

- aioimaplib has no `readline` on the public client; IDLE uses `wait_server_push` / `idle_queue`.
- `authenticate(mechanism, authobject)` is not exposed; use `xoauth2` for OAuth2.
- Generic `uid(command, *args)` covers FETCH/STORE/COPY/MOVE/EXPUNGE only.

## Install

```bash
pip install python-sage-imap[async]
# or: poetry install -E async
```
