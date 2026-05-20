Lesson 6 — Multi-tenant apps and connection policies
====================================================

Goal
----

Wire many mailbox accounts in one application using ``AccountProvider``, connection policies, and the connection registry.

One config per tenant
---------------------

``ImapAccountConfig`` is the unit of connection settings. Store credentials in **your** database or secrets manager; pass them into the ORM at runtime:

.. code-block:: python

   from sage_imap.orm import ConnectionPolicy, ImapAccountConfig, ImapORM

   def open_user_mailbox(user_id: str):
       row = db.get_imap_credentials(user_id)
       config = ImapAccountConfig(
           account_id=user_id,
           host=row.host,
           username=row.email,
           password=row.app_password,
           connection_policy=ConnectionPolicy.POOLED,
           use_pool=True,
       )
       return ImapORM.open(user_id, config=config)

``account_id`` on ``ImapMessage`` lets you audit which tenant touched which UID.

AccountProvider protocol
------------------------

Decouple ORM entry from credential lookup:

.. code-block:: python

   from sage_imap.orm import AccountProvider, ImapAccountConfig

   class DbAccountProvider:
       def get_config(self, account_id: str) -> ImapAccountConfig:
           row = load_from_db(account_id)
           return ImapAccountConfig(
               account_id=account_id,
               host=row.host,
               username=row.username,
               password=row.password,
           )

   provider = DbAccountProvider()
   with ImapORM.open("user-9", provider=provider) as orm:
       orm.select_mailbox("INBOX")
       ...

Reuse an existing session
-------------------------

When you already manage ``IMAPSession`` lifecycle:

.. code-block:: python

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       with ImapORM.open("user-9", session=session) as orm:
           orm.select_mailbox("INBOX")
           for msg in ImapMessage.objects.filter(unread=True).limit(5).iter():
               print(msg.subject)

Connection policies
-------------------

+------------------+------------------------------------------+
| Policy           | When to use                              |
+==================+==========================================+
| ``PER_REQUEST``  | Scripts, one-shot jobs (default)         |
| ``POOLED``       | Web apps sharing clients per account     |
| ``LONG_LIVED``   | Workers holding connections open           |
+------------------+------------------------------------------+

.. code-block:: python

   from sage_imap.orm import ConnectionPolicy, ImapORM

   config = ImapAccountConfig(
       account_id="saas-tenant-1",
       host="imap.example.com",
       username="...",
       password="...",
       connection_policy=ConnectionPolicy.POOLED,
       use_pool=True,
   )

``ImapConnectionRegistry`` (used internally) returns the same pooled session for repeated ``ImapORM.open`` calls with the same config.

OAuth
-----

Pass ``oauth_config`` on ``ImapAccountConfig`` — the ORM forwards it to ``IMAPSession.from_config`` the same way as the core API.

Server dialects
---------------

Set ``dialect="gmail"`` (or another registered hint) when LIST/SEARCH behavior differs by provider. Dialects adjust compatibility shims without changing your queryset code.

Security checklist
------------------

- Never log passwords or refresh tokens.
- Scope ``account_id`` in your app DB — do not trust client-supplied IDs without auth.
- Use TLS (``use_ssl=True``, port 993) in production.

Next: :doc:`07_sync_and_idle`
