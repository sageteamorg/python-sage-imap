Lesson 8 — Gmail, Outlook, and OAuth2
=====================================

Goal
----

Connect to major providers reliably: app passwords where allowed, OAuth2 where required.

Gmail (app password path)
-------------------------

1. Enable 2-Step Verification on your Google account.
2. Create an **App password** for “Mail”.
3. Use:

.. code-block:: python

   with IMAPSession(
       "imap.gmail.com",
       "you@gmail.com",
       "xxxx xxxx xxxx xxxx",  # 16-char app password
   ) as session:
       session.select("INBOX")

.. important::

   Google may block “less secure apps.” App passwords and OAuth are the supported paths — not your normal Gmail password.

Outlook / Microsoft 365
-----------------------

.. code-block:: python

   with IMAPSession(
       "outlook.office365.com",
       "you@outlook.com",
       "your-password-or-app-password",
   ) as session:
       session.select("INBOX")

Corporate tenants often require OAuth2 instead of passwords.

OAuth2 with automatic refresh
-----------------------------

For production integrations (especially Microsoft/Google cloud projects):

.. code-block:: python

   from sage_imap import IMAPSession, OAuth2Config

   oauth = OAuth2Config(
       client_id="...",
       client_secret="...",
       token_url="https://oauth2.googleapis.com/token",
       refresh_token="...",
   )

   with IMAPSession(
       "imap.gmail.com",
       "you@gmail.com",
       oauth_config=oauth,
   ) as session:
       session.select("INBOX")

``connect()`` refreshes access tokens when needed and can persist rotated refresh tokens — see :doc:`../../getting_started/imap_session`.

Custom TLS (corporate proxies, lab servers)
-------------------------------------------

.. code-block:: python

   import ssl
   from sage_imap import ConnectionConfig, IMAPSession

   ctx = ssl.create_default_context()
   config = ConnectionConfig(
       host="imap.corp.example",
       username="user",
       password="secret",
       ssl_context=ctx,
   )

   with IMAPSession.from_config(config) as session:
       session.select("INBOX")

.. warning::

   ``ssl_verify=False`` is only for local labs — never in production.

Provider cheat sheet
--------------------

+------------------+---------------------------+------------------------+
| Provider         | IMAP host                 | Notes                  |
+==================+===========================+========================+
| Gmail            | ``imap.gmail.com``        | App password or OAuth  |
| Outlook.com      | ``outlook.office365.com`` | OAuth common in orgs   |
| Fastmail         | ``imap.fastmail.com``     | App password in settings|
| Generic cPanel   | mail.yourdomain.com       | Often port 993 SSL     |
+------------------+---------------------------+------------------------+

Tips
----

- Store OAuth client secrets outside git; use a secret manager in production.
- Scope tokens to **IMAP only** where the provider allows.
- Rotate refresh tokens when your provider dashboard shows compromise.

Next: :doc:`09_sync_and_idle`
