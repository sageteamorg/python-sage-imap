# IMAPSession — recommended entry point

`IMAPSession` composes the client, UID mailbox service, folders, flags, and sync
helpers behind a single object. Use it for new integrations instead of wiring
services manually.

## Password authentication

```python
from sage_imap import IMAPSession, IMAPSearchCriteria

with IMAPSession("imap.example.com", "user@example.com", "app-password") as session:
    session.select("INBOX")
    result = session.search(IMAPSearchCriteria.UNSEEN)
    for msg in session.iter_messages(result.to_uid_message_set(), batch_size=50):
        print(msg.subject)
```

## OAuth2 with automatic refresh

```python
from sage_imap import IMAPSession, OAuth2Config

oauth = OAuth2Config(
    client_id="...",
    client_secret="...",
    token_url="https://oauth2.googleapis.com/token",
    refresh_token="...",
)

with IMAPSession("imap.gmail.com", "me@gmail.com", oauth_config=oauth) as session:
    session.select("INBOX")
```

`connect()` calls `ensure_access_token()` and rotates `refresh_token` when the
provider returns a new one.

## Custom TLS

```python
import ssl
from sage_imap import ConnectionConfig, IMAPSession

ctx = ssl.create_default_context()
config = ConnectionConfig(
    host="imap.corp.example",
    username="user",
    password="secret",
    ssl_context=ctx,
)

with IMAPSession.from_config(config) as session:  # use config= keyword
    ...
```

Or pass `ssl_verify=False` for lab environments (uses an unverified context).

## SPECIAL-USE folders (Sent, Trash, …)

```python
from sage_imap import SpecialUse

trash = session.special_folder(SpecialUse.TRASH)
sent = session.folders.find_by_special_use(SpecialUse.SENT)
all_special = session.folders.get_special_folders()
```

## Incremental sync (CONDSTORE)

```python
state = session.capture_sync_state("INBOX")
# ... later ...
changed = session.find_changed_since(state)
for msg in session.iter_messages(changed):
    ...
state = session.sync.apply_after_sync(state)
```

## Lower-level access

Properties remain available: `session.client`, `session.mailbox`, `session.folders`,
`session.flags`, `session.sync`.
