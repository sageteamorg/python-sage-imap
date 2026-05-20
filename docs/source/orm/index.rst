IMAP ORM
========

Optional manager/queryset layer over live IMAP (no SQL). Requires::

    pip install python-sage-imap[orm]

Async ORM additionally requires::

    pip install python-sage-imap[orm,async]

Overview
--------

``sage_imap.orm`` provides:

- **Managers & querysets** — ``ImapMessage.objects.filter(unread=True).limit(20)``
- **Explicit pagination** — ``limit()``, ``offset()``, ``cursor(after_uid=...)``
- **Configurable fetch depth** — ``LoadLevel.IDENTITY``, ``HEADERS``, ``FULL``
- **Pydantic schemas** — JSON-friendly API payloads
- **Multi-tenant** — ``account_id`` on all entities; app supplies ``AccountProvider``
- **Sync + async** — ``ImapORM`` and ``AsyncImapORM``
- **CONDSTORE** — ``SyncCheckpoint`` and ``changed_since()``
- **IDLE** — ``IdleSubscription`` / ``AsyncIdleSubscription``

Quick start (sync)
------------------

.. code-block:: python

   from sage_imap.orm import ImapAccountConfig, ImapMessage, ImapORM, LoadLevel
   from sage_imap.orm.schemas import ImapMessageSummarySchema

   config = ImapAccountConfig(
       account_id="tenant-1",
       host="imap.example.com",
       username="user@example.com",
       password="secret",
   )

   with ImapORM.open("tenant-1", config=config) as orm:
       orm.select_mailbox("INBOX")
       for msg in ImapMessage.objects.filter(unread=True).limit(10).iter():
           print(ImapMessageSummarySchema.from_imap_message(msg).model_dump())

Quick start (async)
-------------------

.. code-block:: python

   import asyncio
   from sage_imap.orm import ImapAccountConfig, ImapMessage
   from sage_imap.orm.async_session import AsyncImapORM

   async def main():
       config = ImapAccountConfig(account_id="t1", host="...", username="...", password="...")
       async with AsyncImapORM.open("t1", config=config) as orm:
           await orm.select_mailbox("INBOX")
           msgs = await ImapMessage.objects.filter(unread=True).limit(10).fetch_all_async()
           for msg in msgs:
               print(msg.subject)

   asyncio.run(main())

See ``examples/10_orm_sync.py`` and ``examples/11_orm_async.py``.

Full tutorial
-------------

Step-by-step lessons (install → querysets → sync → async):

:doc:`../tutorials/orm/index`
