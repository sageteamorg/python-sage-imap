.. _imap_session:

IMAPSession (recommended API)
=============================

:class:`~sage_imap.session.IMAPSession` is the primary **sync** entry point. It wires
``IMAPClient``, ``IMAPMailboxUIDService``, folder and flag services, and CONDSTORE sync
behind one object.

Password authentication
-----------------------

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria

   with IMAPSession("imap.example.com", "user@example.com", "app-password") as session:
       session.select("INBOX")
       result = session.search(IMAPSearchCriteria.UNSEEN)
       for msg in session.iter_messages(result.to_uid_message_set(), batch_size=50):
           print(msg.uid, msg.subject)

OAuth2 with refresh
-------------------

.. code-block:: python

   from sage_imap import IMAPSession, OAuth2Config

   oauth = OAuth2Config(
       client_id="...",
       client_secret="...",
       token_url="https://oauth2.googleapis.com/token",
       refresh_token="...",
   )

   with IMAPSession("imap.gmail.com", "me@gmail.com", oauth_config=oauth) as session:
       session.select("INBOX")

``connect()`` calls :func:`~sage_imap.auth.oauth2.ensure_access_token` and updates
refresh tokens when the provider rotates them.

Custom TLS
----------

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

For lab environments you may set ``ssl_verify=False`` on :class:`~sage_imap.services.client.ConnectionConfig`.

SPECIAL-USE folders
-------------------

.. code-block:: python

   from sage_imap import SpecialUse

   trash = session.special_folder(SpecialUse.TRASH)
   sent = session.folders.find_by_special_use(SpecialUse.SENT)

Incremental sync (CONDSTORE)
----------------------------

.. code-block:: python

   state = session.capture_sync_state("INBOX")
   changed = session.find_changed_since(state)
   for msg in session.iter_messages(changed):
       ...
   state = session.sync.apply_after_sync(state)

Lower-level access
------------------

Use ``session.client``, ``session.mailbox``, ``session.folders``, and ``session.flags``
when you need direct service APIs.
