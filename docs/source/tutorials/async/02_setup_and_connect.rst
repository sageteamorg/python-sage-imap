Lesson 2 — Setup and first async connection
===========================================

Goal
----

Install the ``[async]`` extra, connect with ``AsyncIMAPSession``, and print INBOX counts.

Sync vs async — setup
---------------------

Same environment variables as :doc:`../sync/02_setup_and_connect`. Same hosts and passwords.

Step 1 — Install
----------------

.. code-block:: bash

   pip install python-sage-imap[async]

Step 2 — Minimal script
-----------------------

.. code-block:: python

   import asyncio
   import os

   from sage_imap.aio import AsyncIMAPSession
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.exceptions import IMAPAuthenticationError, IMAPConnectionError

   async def main() -> None:
       host = os.environ["IMAP_HOST"]
       user = os.environ["IMAP_USER"]
       password = os.environ["IMAP_PASSWORD"]

       try:
           async with AsyncIMAPSession(host, user, password) as session:
               print("Connected.")
               await session.select("INBOX")
               result = await session.search(IMAPSearchCriteria.ALL)
               print(f"INBOX: {result.message_count} messages")
       except IMAPConnectionError as exc:
           print(f"Connection problem: {exc}")
       except IMAPAuthenticationError as exc:
           print(f"Auth failed: {exc}")

   if __name__ == "__main__":
       asyncio.run(main())

Compared to sync
~~~~~~~~~~~~~~~~

+----------------------------------+----------------------------------+
| Sync                             | Async                            |
+==================================+==================================+
| ``with IMAPSession(...)``        | ``async with AsyncIMAPSession``  |
| ``session.select("INBOX")``      | ``await session.select(...)``    |
| ``session.search(...)``          | ``await session.search(...)``    |
| Run script: ``python app.py``    | Need ``asyncio.run(main())``     |
+----------------------------------+----------------------------------+

.. tip::

   Forgetting ``await`` is the most common bug — Python will warn that a coroutine was never awaited.

Step 3 — ``from_config`` variant
--------------------------------

.. code-block:: python

   from sage_imap import ConnectionConfig
   from sage_imap.aio import AsyncIMAPSession

   config = ConnectionConfig(host=host, username=user, password=password)
   async with AsyncIMAPSession.from_config(config) as session:
       await session.select("INBOX")

``ConnectionConfig`` is shared between sync and async.

Exercise
--------

Wrap ``main()`` so ``asyncio.run`` is only called when ``__name__ == "__main__"`` (makes importing testable).

Next: :doc:`03_explore_mailbox`
