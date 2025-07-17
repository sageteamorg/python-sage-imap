==============================
Python Sage IMAP Documentation
==============================

.. image:: https://badge.fury.io/py/python-sage-imap.svg
   :target: https://badge.fury.io/py/python-sage-imap
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/python-sage-imap.svg
   :target: https://pypi.org/project/python-sage-imap/
   :alt: Python versions

.. image:: https://pepy.tech/badge/python-sage-imap
   :target: https://pepy.tech/project/python-sage-imap
   :alt: Downloads

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

.. image:: https://codecov.io/gh/sageteamorg/python-sage-imap/graph/badge.svg?token=I10LGK910X
   :target: https://codecov.io/gh/sageteamorg/python-sage-imap
   :alt: Code coverage

**A robust, production-ready Python library for IMAP email operations with advanced features including connection pooling, retry logic, monitoring, and comprehensive email management.**

Overview
========

Python Sage IMAP is designed for developers who need reliable, scalable email processing capabilities. Unlike basic IMAP libraries, it provides enterprise-grade features that handle real-world challenges like connection management, error recovery, and performance monitoring.

Key Features
============

🔄 **Connection Management**
   Advanced connection pooling with automatic retry logic

📊 **Monitoring & Metrics**
   Built-in performance tracking and operation statistics

🔍 **Advanced Search**
   Powerful email search with multiple criteria and filters

📁 **Folder Operations**
   Complete folder management (create, rename, delete, list)

🏷️ **Flag Management**
   Comprehensive flag operations with bulk support

📧 **Email Processing**
   Rich email parsing with attachment handling

🔐 **Security**
   SSL/TLS support with secure authentication

⚡ **Performance**
   Optimized for handling large mailboxes efficiently

🛡️ **Error Handling**
   Comprehensive exception handling and recovery

🎨 **Modern API**
   Clean, intuitive interface with type hints

Quick Start
===========

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet

   # Connect to IMAP server
   with IMAPClient(host="imap.gmail.com", username="user@gmail.com", password="password") as client:
       # Select mailbox
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Search for emails
       criteria = IMAPSearchCriteria().from_address("sender@example.com")
       messages = mailbox.search(criteria)
       
       # Process messages
       for message in messages:
           print(f"Subject: {message.subject}")
           print(f"From: {message.sender}")

Installation
============

.. code-block:: bash

   pip install python-sage-imap

Requirements
============

- Python 3.7+
- IMAP server access
- SSL/TLS support (recommended)

Documentation Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/index

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
