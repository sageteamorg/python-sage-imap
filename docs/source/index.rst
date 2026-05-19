==============================
Python Sage IMAP Documentation
==============================

.. image:: https://badge.fury.io/py/python-sage-imap.svg
   :target: https://badge.fury.io/py/python-sage-imap
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/python-sage-imap.svg
   :target: https://pypi.org/project/python-sage-imap/
   :alt: Python versions

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

**Production-oriented IMAP for Python 3.10+** — UID-first operations, CONDSTORE sync, IDLE, OAuth2, SPECIAL-USE folders, and optional async IMAP.

Overview
========

Python Sage IMAP helps you build reliable email integrations: search and fetch with UIDs,
stream large mailboxes, sync incrementally, and optionally run an asyncio-native client.

**Release 2.0.0** adds ``sage_imap.aio`` (``pip install python-sage-imap[async]``). The sync
API remains the default and is stdlib-only.

Key features
============

- :doc:`getting_started/imap_session` — ``IMAPSession`` facade (recommended)
- :doc:`getting_started/async_api` — ``AsyncIMAPSession`` and IDLE
- UID search/fetch, ``ParseMode``, bulk flags and folder ops
- CONDSTORE incremental sync and IDLE notifications
- OAuth2 with token refresh, custom TLS, connection pooling and metrics

Quick start (sync)
==================

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria

   with IMAPSession("imap.example.com", "user@example.com", "secret") as session:
       session.select("INBOX")
       result = session.search(IMAPSearchCriteria.UNSEEN)
       for msg in session.iter_messages(result.to_uid_message_set()):
           print(msg.subject)

Quick start (async)
===================

.. code-block:: python

   import asyncio
   from sage_imap.aio import AsyncIMAPSession
   from sage_imap.helpers.search import IMAPSearchCriteria

   async def main():
       async with AsyncIMAPSession("imap.example.com", "user", "secret") as session:
           await session.select("INBOX")
           result = await session.search(IMAPSearchCriteria.ALL)
           async for msg in session.iter_messages(result.to_uid_message_set()):
               print(msg.subject)

   asyncio.run(main())

Installation
============

.. code-block:: bash

   pip install python-sage-imap
   pip install python-sage-imap[async]   # optional

Requirements: **Python 3.10+**, IMAP server access, TLS recommended.

Documentation contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/index

.. toctree::
   :maxdepth: 2
   :caption: API guides

   getting_started/imap_session
   getting_started/async_api
   getting_started/migration_v2

.. toctree::
   :maxdepth: 2
   :caption: Examples & Tutorials

   getting_started/examples/index

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   troubleshooting
   faq
   contributing
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
