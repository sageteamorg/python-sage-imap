Lesson 7 — Folders and SPECIAL-USE (async)
==========================================

Goal
----

Resolve Trash/Sent without hard-coded names using async folder helpers.

Same concepts as :doc:`../sync/07_folders_and_special_use`.

SPECIAL-USE
-----------

.. code-block:: python

   import asyncio

   from sage_imap import SpecialUse
   from sage_imap.aio import AsyncIMAPSession

   async def main() -> None:
       async with AsyncIMAPSession(host, user, password) as session:
           trash = await session.special_folder(SpecialUse.TRASH)
           sent = await session.special_folder(SpecialUse.SENT)
           print("Trash:", trash, "Sent:", sent)

   asyncio.run(main())

Compared to sync
~~~~~~~~~~~~~~~~

- Sync: ``session.special_folder(SpecialUse.TRASH)``
- Async: ``await session.special_folder(...)`` — the session method is async because it may query the server.

Find by attribute
-----------------

.. code-block:: python

   info = await session.folders.find_by_special_use(SpecialUse.SENT)
   if info:
       print(info.name)

List folders
--------------

.. code-block:: python

   folders = await session.folders.list_folders()
   for info in folders[:15]:
       print(info.name, getattr(info, "unseen_count", None))

Namespaces
----------

.. code-block:: python

   ns = await session.namespace()
   print(ns.personal)

Next: :doc:`08_auth_providers`
