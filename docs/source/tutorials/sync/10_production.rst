Lesson 10 — Production playbook
===============================

Goal
----

Ship scripts that fail gracefully, scale to large mailboxes, and follow security conventions.

Error handling template
-----------------------

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria
   from sage_imap.exceptions import (
       IMAPAuthenticationError,
       IMAPConnectionError,
       IMAPMessageError,
       IMAPSearchError,
   )

   def sync_inbox() -> None:
       try:
           with IMAPSession(host, user, password) as session:
               session.select("INBOX")
               result = session.search(IMAPSearchCriteria.UNSEEN)
               if not result.success:
                   raise IMAPSearchError(result.error_message or "search failed")
               for msg in session.iter_messages(result.to_uid_message_set(), batch_size=50):
                   process(msg)  # your business logic
       except IMAPConnectionError:
           # retry with backoff, alert ops
           raise
       except IMAPAuthenticationError:
           # refresh OAuth / rotate app password — do not spin forever
           raise
       except IMAPMessageError:
           # single-message corruption — log UID and continue if safe
           raise

Performance checklist
---------------------

- [ ] Search before ``ParseMode.FULL``
- [ ] Use ``batch_size`` tuned to your network (25–100 typical)
- [ ] Use CONDSTORE instead of full mailbox scans
- [ ] Avoid parallel commands on **one** connection (IMAP is single-stream)
- [ ] Reuse one session per job; reconnect on failure

Security checklist
--------------------

- [ ] Credentials from environment or secret store
- [ ] TLS on (default port 993)
- [ ] OAuth or app passwords — no shared human passwords in CI
- [ ] Least-privilege OAuth scopes
- [ ] Log UIDs and subjects carefully (PII)

Observability
-------------

Enable connection metrics when debugging slow servers:

.. code-block:: python

   from sage_imap import ConnectionConfig, IMAPSession

   config = ConnectionConfig(
       host=host,
       username=user,
       password=password,
       enable_monitoring=True,
   )
   with IMAPSession.from_config(config) as session:
       ...
       metrics = session.client.get_metrics()
       print(metrics.average_response_time)

Lower-level control
-------------------

Need transport-level access? Use:

- ``session.client`` — connection and capabilities
- ``session.mailbox`` — UID operations
- ``session.folders`` / ``session.flags`` — specialized services

See :doc:`../../getting_started/imap_session` and :doc:`../../getting_started/best_practices`.

When to learn async
-------------------

If your program already uses ``asyncio`` (websockets, HTTP, multiple waits), continue with the :doc:`../async/index` track. Otherwise, sync is simpler and enough for cron/CLI tools.

Congratulations
---------------

You completed the sync track. You can build real mailbox tools without a backend framework — connect, search by UID, read efficiently, act on messages, authenticate safely, sync incrementally, and operate responsibly in production.
