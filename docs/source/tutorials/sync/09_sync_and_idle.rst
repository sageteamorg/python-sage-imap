Lesson 9 — Incremental sync (CONDSTORE) and IDLE
================================================

Goal
----

Run periodic jobs that only process **changed** messages, and optionally wait for new mail instead of polling.

Part A — Incremental sync with CONDSTORE
----------------------------------------

If your server supports CONDSTORE (most modern providers do), snapshot state and ask “what changed?”:

.. code-block:: python

   from sage_imap import IMAPSession

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")

       # First run — baseline
       state = session.capture_sync_state("INBOX")
       print("Baseline UIDVALIDITY:", state.uid_validity)

       # ... later run (new script invocation) ...
       session.select("INBOX")
       changed = session.find_changed_since(state)
       if changed.is_empty():
           print("No changes since last sync.")
       else:
           for msg in session.iter_messages(changed, batch_size=50):
               print("Changed:", msg.uid, msg.subject)

       # After successful processing, advance state
       state = session.sync.apply_after_sync(state)

.. tip::

   Persist ``state`` to disk (JSON/pickle) or a small database between runs. Pair ``uid_validity`` with your saved state — if validity changes, the folder was reset and you must resync fully.

When CONDSTORE is unavailable, fall back to time-based search (``SINCE``) or full scans with tight ``ParseMode.HEADERS``.

Part B — IDLE (push-style notifications)
----------------------------------------

:class:`~sage_imap.services.idle.IMAPIdleSession` blocks until the server reports activity (new mail, flags, etc.):

.. code-block:: python

   from sage_imap import IMAPSession
   from sage_imap.services.idle import IMAPIdleSession

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       with IMAPIdleSession(session.client, "INBOX") as idle:
           result = idle.wait(timeout=120.0)
           for event in result.events:
               print(event.event_type, event.sequence)

For long-running watchers, see ``IMAPIdleWatcher`` in the API reference.

Sync vs poll — when to use which
--------------------------------

+------------------+-------------------------+-------------------------+
| Pattern          | Good for                | Drawback                |
+==================+=========================+=========================+
| Cron + CONDSTORE | Scripts every N minutes | Not instant             |
| IDLE             | Near-real-time bots     | Holds connection open   |
| Tight poll loop  | Simple prototypes       | Wastes battery/bandwidth|
+------------------+-------------------------+-------------------------+

Exercise
--------

1. Save sync state to a JSON file after each run.
2. On the next run, only print subjects of changed messages.
3. Optional: run IDLE for 60 seconds and log events.

Next: :doc:`10_production`
