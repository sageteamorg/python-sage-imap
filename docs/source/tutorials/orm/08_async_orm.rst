Lesson 8 — Async ORM
====================

Goal
----

Run the same manager/queryset patterns inside ``asyncio`` with ``AsyncImapORM``.

Install
-------

.. code-block:: bash

   pip install python-sage-imap[orm,async]

Open and query
--------------

.. code-block:: python

   import asyncio
   from sage_imap.orm import ImapAccountConfig, ImapMessage, LoadLevel
   from sage_imap.orm.async_session import AsyncImapORM

   async def main():
       config = ImapAccountConfig(
           account_id="demo",
           host="imap.example.com",
           username="you@example.com",
           password="secret",
       )
       async with AsyncImapORM.open("demo", config=config) as orm:
           await orm.select_mailbox("INBOX")
           qs = (
               ImapMessage.objects.filter(unread=True)
               .limit(10)
               .with_load_level(LoadLevel.HEADERS)
           )
           async for msg in qs.iter_async():
               print(msg.uid, msg.subject)

   asyncio.run(main())

Sync vs async API map
---------------------

+----------------------+---------------------------+
| Sync                 | Async                     |
+======================+===========================+
| ``ImapORM.open()``   | ``AsyncImapORM.open()``   |
| ``orm.select_mailbox`` | ``await orm.select_mailbox`` |
| ``qs.iter()``        | ``async for ... iter_async()`` |
| ``qs.fetch_all()``   | ``await qs.fetch_all_async()`` |
| ``msg.mark_seen()``  | ``await msg.amark_seen()`` |
| ``cp.apply(backend)`` | ``await cp.apply_async(backend)`` |
| ``IdleSubscription`` | ``AsyncIdleSubscription`` |
| ``ImapFolder.objects.list()`` | Same sync call inside ``async with`` (no async list yet) |
+----------------------+---------------------------+

Fetch all in one await
----------------------

.. code-block:: python

   msgs = await ImapMessage.objects.filter(unread=True).limit(5).fetch_all_async()

Checkpoints async
-----------------

.. code-block:: python

   cp = await SyncCheckpoint.objects.for_mailbox_async("demo", "INBOX")
   await cp.apply_async(orm.backend)

Mixing sync and async ORM
-------------------------

Do **not** call blocking ``iter()`` inside a running event loop. Use the async iterators and ``a*`` methods exclusively in asyncio apps.

Runnable example: ``examples/11_orm_async.py``.

You are done
------------

You can now:

- Choose between session API and ORM for new features
- Build tenant-safe mail features with schemas and pagination
- Incrementally sync and react to new mail

Reference: :doc:`../../orm/index` · Core async tutorial: :doc:`../async/index`
