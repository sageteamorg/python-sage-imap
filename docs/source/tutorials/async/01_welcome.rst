Lesson 1 — Welcome: async mail without a backend
================================================

Goal
----

Understand when the **async** track is worth it and how it differs from the :doc:`../sync/01_welcome` mental model.

Same problem, different concurrency style
-----------------------------------------

You are still a **client** talking IMAP to your provider. You still do not need a web framework or database.

The async track uses:

- ``async def main()``
- ``async with AsyncIMAPSession(...)``
- ``await session.select(...)``
- ``async for msg in session.iter_messages(...)``

Compared to sync
----------------

+----------------------+---------------------------+-------------------------------+
|                      | Sync                      | Async                         |
+======================+===========================+===============================+
| Import               | ``from sage_imap import`` | ``from sage_imap.aio import`` |
| Session class        | ``IMAPSession``           | ``AsyncIMAPSession``          |
| Connect              | ``with session:``         | ``async with session:``       |
| Each IMAP call       | blocks the thread           | ``await`` yields to event loop|
| Iterate messages     | ``for msg in ...``        | ``async for msg in ...``      |
| Extra dependency     | stdlib only               | ``pip install ...[async]``    |
+----------------------+---------------------------+-------------------------------+

.. tip::

   **Choose async** if your app is already asyncio-based (FastAPI, discord.py, aiohttp bots). **Choose sync** for simple scripts and cron — less conceptual overhead.

One connection, one command stream (both tracks)
------------------------------------------------

Whether sync or async, **one IMAP connection processes one command at a time**. Async does not mean parallel FETCH on a single client; the transport uses a lock to serialize commands.

What does improve with async?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While ``await`` waits for IMAP, your event loop can run **other** tasks (HTTP health checks, timers, other connections in *other* sessions).

Install
-------

.. code-block:: bash

   pip install python-sage-imap[async]

Next: :doc:`02_setup_and_connect`
