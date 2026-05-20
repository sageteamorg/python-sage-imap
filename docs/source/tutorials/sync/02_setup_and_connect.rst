Lesson 2 — Setup and your first connection
==========================================

Goal
----

Install the library, store credentials safely, connect to your provider, and print proof that INBOX exists.

Step 1 — Virtual environment
----------------------------

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate    # Windows: .venv\Scripts\activate
   pip install python-sage-imap

.. tip::

   A virtual environment keeps this project’s packages separate from other Python projects on your machine.

Step 2 — Credentials as environment variables
---------------------------------------------

Never commit passwords. Create a small module or export variables in your shell:

.. code-block:: bash

   export IMAP_HOST=imap.gmail.com
   export IMAP_USER=you@gmail.com
   export IMAP_PASSWORD=your-app-password

In Python:

.. code-block:: python

   import os

   HOST = os.environ["IMAP_HOST"]
   USER = os.environ["IMAP_USER"]
   PASSWORD = os.environ["IMAP_PASSWORD"]

.. important::

   For Gmail and many providers, use an **app password** or OAuth — not your normal login password. Lesson 8 covers provider-specific setup.

Step 3 — Minimal connect script
-------------------------------

Save as ``check_inbox.py``:

.. code-block:: python

   import os

   from sage_imap import IMAPSession, IMAPSearchCriteria
   from sage_imap.exceptions import IMAPAuthenticationError, IMAPConnectionError

   def main() -> None:
       host = os.environ["IMAP_HOST"]
       user = os.environ["IMAP_USER"]
       password = os.environ["IMAP_PASSWORD"]

       try:
           with IMAPSession(host, user, password) as session:
               print("Connected.")
               session.select("INBOX")
               result = session.search(IMAPSearchCriteria.ALL)
               print(f"INBOX contains {result.message_count} messages (UID search).")
       except IMAPConnectionError as exc:
           print(f"Network or TLS problem: {exc}")
       except IMAPAuthenticationError as exc:
           print(f"Login rejected — check user/password/IMAP enabled: {exc}")

   if __name__ == "__main__":
       main()

Run:

.. code-block:: bash

   python check_inbox.py

Expected output (numbers vary):

.. code-block:: text

   Connected.
   INBOX contains 42 messages (UID search).

What the code does, line by line
--------------------------------

1. **``IMAPSession(host, user, password)``** — builds a client configuration (port 993, SSL on by default).
2. **``with ... as session``** — calls ``connect()`` on enter and ``close()`` on exit.
3. **``session.select("INBOX")``** — tells the server which folder is active for search/fetch.
4. **``session.search(IMAPSearchCriteria.ALL)``** — UID SEARCH for every message; returns a result object with ``message_count``.

Step 4 — Understand failures
----------------------------

+---------------------------+----------------------------------------+
| Exception                 | Usual cause                            |
+===========================+========================================+
| ``IMAPConnectionError``   | Wrong host, firewall, TLS, port        |
| ``IMAPAuthenticationError`` | Bad password, IMAP disabled, 2FA   |
+---------------------------+----------------------------------------+

.. tip::

   Test the same host/user/password in a desktop mail client first. If that fails, fix provider settings before debugging Python.

Optional: explicit configuration
--------------------------------

Use :class:`~sage_imap.services.client.ConnectionConfig` when you need timeouts, retries, or custom TLS:

.. code-block:: python

   from sage_imap import ConnectionConfig, IMAPSession

   config = ConnectionConfig(
       host=os.environ["IMAP_HOST"],
       username=os.environ["IMAP_USER"],
       password=os.environ["IMAP_PASSWORD"],
       port=993,
       use_ssl=True,
       timeout=30.0,
   )

   with IMAPSession.from_config(config) as session:
       session.select("INBOX")

Exercise
--------

1. Print ``result.success`` and ``result.error_message`` if search fails.
2. Log the server capabilities once: ``session.client.transport.get_capabilities()`` (advanced peek — not required for daily use).

Next: :doc:`03_explore_mailbox`
