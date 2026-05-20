.. _introduction:

Introduction to Python Sage IMAP
==================================

**Python Sage IMAP** is a library for building reliable IMAP clients in Python. Use it for mail sync, automation, or backend services that need search, fetch, folders, flags, and incremental updates without hand-rolling ``imaplib`` for every feature.

What is Python Sage IMAP?
--------------------------

Python Sage IMAP is a modern library for IMAP email operations on **Python 3.10+**. The sync stack uses ``imaplib``; **v2** adds an optional async API (``sage_imap.aio`` via ``aioimaplib``). Use :class:`~sage_imap.session.IMAPSession` as the recommended sync entry point. It's designed for developers who need reliable, scalable email processing capabilities without the complexity of low-level IMAP protocol handling.

Why Choose Python Sage IMAP?
-----------------------------

Enterprise-Grade Features
~~~~~~~~~~~~~~~~~~~~~~~~~~

Unlike basic IMAP libraries, Python Sage IMAP provides enterprise-grade features:

- **Connection Management**: Advanced connection pooling with automatic retry logic
- **Performance Monitoring**: Built-in metrics and performance tracking
- **Error Handling**: Comprehensive exception handling with meaningful error messages
- **Resource Management**: Proper cleanup and connection lifecycle management
- **Type Safety**: Full type hint support for better IDE integration

Real-World Problem Solving
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python Sage IMAP addresses common challenges developers face:

- **Reliability**: Automatic retries and error recovery for unstable connections
- **Performance**: Optimized for handling large mailboxes and high-volume operations
- **Maintainability**: Clean, object-oriented API that's easy to understand and maintain
- **Scalability**: Connection pooling and efficient resource utilization

Modern Development Experience
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Built with modern Python best practices:

- **Pythonic API**: Intuitive method names and consistent patterns
- **Context Managers**: Proper resource management with ``with`` statements
- **Type Hints**: Complete type annotations for better IDE support
- **Documentation**: Comprehensive docs with working examples

Key features
------------

**Connection management**

- Optional connection pooling (``use_pool=True``)
- Retries with exponential backoff
- Health checks and keepalive
- TLS with custom ``SSLContext`` or OAuth2

**Operations**

- UID search and batched fetch (``iter_uid_fetch`` / ``iter_messages``)
- Folder and flag services with bulk STORE
- CONDSTORE incremental sync and IDLE
- SPECIAL-USE folder resolution (Sent, Trash, and related mailboxes)

**Developer experience**

- Type hints and structured exceptions
- :class:`~sage_imap.session.IMAPSession` facade for typical apps
- Optional ``sage_imap.aio`` for asyncio

Who Should Use Python Sage IMAP?
---------------------------------

Perfect for Developers Who Need:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Email Integration**: Adding email capabilities to existing applications
- **Email Automation**: Building automated email processing systems
- **Email Management**: Creating email management and organization tools
- **Email Analytics**: Analyzing email data and patterns
- **Email Migration**: Moving emails between systems or providers

Common Use Cases:
~~~~~~~~~~~~~~~~~

- **Customer Support Systems**: Processing support tickets from email
- **Marketing Automation**: Managing email campaigns and responses
- **Data Processing**: Extracting and processing email data
- **Backup and Archiving**: Backing up and organizing email data
- **Integration Projects**: Connecting email systems with other applications

Getting Started is Easy
------------------------

With just a few lines of code, you can connect to any IMAP server and start processing emails:

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   from sage_imap.helpers.search import IMAPSearchCriteria

   # Connect to your IMAP server
   with IMAPClient(
       host="imap.example.com",
       username="your_username",
       password="your_password"
   ) as client:
       # Select a mailbox
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Search for emails
       criteria = IMAPSearchCriteria().from_address("sender@example.com")
       messages = mailbox.search(criteria)
       
       # Process messages
       for message in messages:
           print(f"Subject: {message.subject}")
           print(f"From: {message.sender}")

What Makes It Different?
------------------------

Compared to Raw ``imaplib``:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - Raw ``imaplib``
     - Python Sage IMAP
   * - Connection Management
     - Manual handling
     - Automatic pooling & retry
   * - Error Handling
     - Basic exceptions
     - Comprehensive error types
   * - Search Capabilities
     - Raw IMAP syntax
     - Intuitive criteria builder
   * - Performance
     - Basic operations
     - Optimized with monitoring
   * - Development Experience
     - Low-level protocol
     - High-level, pythonic API
   * - Production Ready
     - Requires custom logic
     - Built-in enterprise features

Compared to Other Libraries:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **More Comprehensive**: Covers all IMAP operations with advanced features
- **Better Performance**: Built-in optimization and monitoring
- **Production Ready**: Designed for enterprise use with proper error handling
- **Modern API**: Clean, intuitive interface with type hints
- **Active Development**: Regular updates and improvements

Architecture Overview
----------------------

Python Sage IMAP follows a modular architecture:

**Core Services**:
   - ``IMAPClient``: Connection management and core operations
   - ``IMAPMailboxService``: Email operations and message handling
   - ``IMAPFolderService``: Folder management and organization

**Helper Modules**:
   - ``IMAPSearchCriteria``: Search query building
   - ``MessageSet``: Message collection handling
   - ``Enums``: Standard flags and constants

**Data Models**:
   - ``Message``: Email message representation
   - ``Email``: Enhanced email model with parsing
   - ``Attachment``: File attachment handling

**Exception Handling**:
   - Specialized exceptions for different error types
   - Meaningful error messages and context
   - Proper error recovery strategies

Next Steps
----------

Ready to get started? Here's what to do next:

1. **Install the Library**: :doc:`installation` - Get Python Sage IMAP installed
2. **Learn the Basics**: :doc:`first_steps` - Make your first connection
3. **Follow the tutorials**: :doc:`../tutorials/index` - Sync and async tracks from scratch to production
4. **Understand Concepts**: :doc:`terminologies` - Learn key IMAP concepts

Or jump straight to a specific topic:

- :doc:`features` - Explore all available features
- :doc:`search` - Learn about search capabilities
- :doc:`message_set` - Understand message handling
- :doc:`headers` - Work with email headers

Need Help?
----------

- **Documentation**: Complete guides and API reference
- **Examples**: Working code examples for common tasks
- **Community**: GitHub discussions and issue tracking
- **Support**: Professional support options available

Python Sage IMAP is designed to make email processing straightforward and reliable. Let's get you started on your email automation journey!
