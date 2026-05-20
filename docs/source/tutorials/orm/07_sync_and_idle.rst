Lesson 7 — Incremental sync (CONDSTORE) and IDLE
================================================

Goal
----

Sync only changed messages since the last run and optionally wait for new mail with IDLE — using ORM checkpoints and subscriptions.

Background
----------

- **CONDSTORE** — servers expose ``MODSEQ``; ``CHANGEDSINCE`` finds altered messages.
- **IDLE** — push-style notification while the connection waits (RFC 2177).

The core library exposes ``MailboxSyncState``; the ORM wraps it as ``SyncCheckpoint``.

Capture a checkpoint
--------------------

Inside an active ``ImapORM`` session:

.. code-block:: python

   from sage_imap.orm import SyncCheckpoint

   with ImapORM.open("user-1", config=config) as orm:
       orm.select_mailbox("INBOX")
       cp = SyncCheckpoint.objects.for_mailbox("user-1", "INBOX")
       # cp.state holds uidvalidity, highest modseq, etc.
       save_to_database(cp)   # your persistence layer

Query changed messages
----------------------

Restore a previously saved ``MailboxSyncState`` (or checkpoint) and filter:

.. code-block:: python

   with ImapORM.open("user-1", config=config) as orm:
       orm.select_mailbox("INBOX")
       state = load_state_from_database()
       qs = ImapMessage.objects.changed_since(state).with_load_level(LoadLevel.HEADERS)
       for msg in qs.iter():
           handle_change(msg)
       cp = SyncCheckpoint("user-1", "INBOX", state=state)
       cp.refresh(orm.backend)
       cp.apply(orm.backend)   # advance MODSEQ after successful processing
       save_to_database(cp.state)

``apply()`` updates the stored MODSEQ so the next run only sees newer changes.

Typical worker loop
-------------------

.. code-block:: python

   def sync_inbox(account_id: str, config: ImapAccountConfig) -> None:
       state = load_checkpoint(account_id, "INBOX")
       with ImapORM.open(account_id, config=config) as orm:
           orm.select_mailbox("INBOX")
           qs = ImapMessage.objects.changed_since(state).limit(500)
           batch = list(qs.iter())
           if not batch:
               return
           for msg in batch:
               index_message(msg)
           cp = SyncCheckpoint(account_id, "INBOX", state=state)
           cp.refresh(orm.backend).apply(orm.backend)
           save_checkpoint(cp.state)

Requires server support for CONDSTORE (Gmail, Fastmail, Dovecot, and most modern hosts).

IDLE — wait for new mail
------------------------

Use a **dedicated** connection for IDLE (do not share with busy workers):

.. code-block:: python

   from sage_imap.orm import IdleSubscription

   with IdleSubscription.for_mailbox("user-1", "INBOX", config=config) as sub:
       while True:
           events = sub.wait(timeout=120.0)
           if events:
               print("Mailbox changed:", events)
               break

``IdleSubscription`` opens its own ``ImapORM`` + ``IMAPIdleSession``. Process new mail in a separate short-lived ORM session.

Async IDLE
----------

See :doc:`08_async_orm` for ``AsyncIdleSubscription`` and ``await checkpoint.apply_async()``.

Relation to session tutorials
-----------------------------

Sync lesson :doc:`../sync/09_sync_and_idle` covers the same concepts on ``IMAPSession``. The ORM adds checkpoint helpers and queryset ``changed_since()`` but the underlying protocol is identical.

Next: :doc:`08_async_orm`
