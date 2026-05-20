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

Production-oriented IMAP for **Python 3.10+**: UID search and fetch, CONDSTORE sync, IDLE, OAuth2, SPECIAL-USE folders, and an optional async client (``sage_imap.aio``).

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

Install with ``pip install python-sage-imap`` (add ``[async]`` for the asyncio API).

.. toctree::
   :maxdepth: 1
   :caption: Quick start

   getting_started/installation
   getting_started/first_steps
   getting_started/imap_session
   getting_started/async_api
   getting_started/migration_v2

.. toctree::
   :maxdepth: 1
   :caption: User guide

   getting_started/introduction
   getting_started/what_is_imap
   getting_started/terminologies
   getting_started/features
   getting_started/search
   getting_started/message_set
   getting_started/headers
   getting_started/best_practices
   getting_started/common_patterns

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/index

.. toctree::
   :maxdepth: 1
   :caption: IMAP ORM

   orm/index

.. toctree::
   :maxdepth: 1
   :caption: Project

   troubleshooting
   faq
   contributing
   changelog

Indices
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
