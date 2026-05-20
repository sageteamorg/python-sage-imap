Lesson 8 — Providers and OAuth2 (async)
=======================================

Goal
----

Authenticate to Gmail, Outlook, or custom hosts with passwords or OAuth2 in asyncio programs.

Provider hosts
--------------

Identical to :doc:`../sync/08_auth_providers` — only the session constructor and ``await connect()`` differ.

Password auth
-------------

.. code-block:: python

   async with AsyncIMAPSession("imap.gmail.com", user, app_password) as session:
       await session.select("INBOX")

OAuth2
------

.. code-block:: python

   from sage_imap import OAuth2Config
   from sage_imap.aio import AsyncIMAPSession

   oauth = OAuth2Config(
       client_id="...",
       client_secret="...",
       token_url="https://oauth2.googleapis.com/token",
       refresh_token="...",
   )

   async with AsyncIMAPSession(
       "imap.gmail.com",
       "you@gmail.com",
       oauth_config=oauth,
   ) as session:
       await session.select("INBOX")

Compared to sync
~~~~~~~~~~~~~~~~

+--------------------------------+--------------------------------+
| Sync OAuth refresh             | Async OAuth refresh            |
+================================+================================+
| stdlib HTTP                    | ``httpx`` (``[async]`` extra)  |
+--------------------------------+--------------------------------+

Token refresh runs during ``await session.connect()`` without blocking other coroutines on the event loop (unlike blocking sync I/O).

Custom TLS
----------

.. code-block:: python

   from sage_imap import ConnectionConfig
   from sage_imap.aio import AsyncIMAPSession

   config = ConnectionConfig(host=host, username=user, password=password)
   async with AsyncIMAPSession.from_config(config) as session:
       await session.select("INBOX")

Next: :doc:`09_sync_and_idle`
