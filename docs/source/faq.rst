.. _faq:

Frequently Asked Questions (FAQ)
================================

This section covers the most frequently asked questions about Python Sage IMAP.

General Questions
-----------------

What is Python Sage IMAP?
~~~~~~~~~~~~~~~~~~~~~~~~~~

Python Sage IMAP is a robust, production-ready Python library for IMAP email operations. It provides enterprise-grade features including connection pooling, retry logic, monitoring, and comprehensive email management capabilities.

Unlike basic IMAP libraries, Python Sage IMAP is designed to handle real-world challenges like connection management, error recovery, and performance optimization.

How is it different from Python's built-in imaplib?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python Sage IMAP provides several advantages over the built-in ``imaplib``:

- **Higher-level API**: Simplified, object-oriented interface
- **Connection management**: Automatic connection pooling and retry logic
- **Error handling**: Comprehensive exception handling with meaningful error messages
- **Performance**: Built-in optimizations for large mailboxes
- **Monitoring**: Built-in metrics and performance tracking
- **Type hints**: Full type hint support for better development experience
- **Search capabilities**: Advanced search with intuitive criteria building
- **Email parsing**: Rich email parsing with attachment handling

What Python versions are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python Sage IMAP supports Python 3.7 and later. We recommend using the latest stable Python version for the best experience.

Is it production-ready?
~~~~~~~~~~~~~~~~~~~~~~~

Yes, Python Sage IMAP is designed for production use with:

- Comprehensive error handling and recovery
- Connection pooling for better resource management
- Retry logic with exponential backoff
- Performance monitoring and metrics
- Extensive test coverage
- Active maintenance and support

Installation and Setup
----------------------

How do I install Python Sage IMAP?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can install Python Sage IMAP using pip:

.. code-block:: bash

   pip install python-sage-imap

Or using Poetry:

.. code-block:: bash

   poetry add python-sage-imap

Do I need any additional dependencies?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python Sage IMAP has minimal dependencies. All required packages are automatically installed when you install the library. The main dependencies are:

- Standard Python libraries (``imaplib``, ``email``, ``ssl``, etc.)
- No external dependencies for core functionality

Can I use it with virtual environments?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, we strongly recommend using virtual environments. Here's how:

.. code-block:: bash

   # Create virtual environment
   python -m venv venv
   
   # Activate it
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install the package
   pip install python-sage-imap

Connection and Authentication
-----------------------------

Which IMAP servers are supported?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python Sage IMAP works with any IMAP-compliant server, including:

- Gmail (imap.gmail.com)
- Outlook/Hotmail (outlook.office365.com)
- Yahoo Mail (imap.mail.yahoo.com)
- iCloud Mail (imap.mail.me.com)
- Custom/corporate IMAP servers

How do I connect to Gmail?
~~~~~~~~~~~~~~~~~~~~~~~~~~

For Gmail, you need to use app-specific passwords:

.. code-block:: python

   from sage_imap.services import IMAPClient
   
   # Use app-specific password, not your regular password
   client = IMAPClient(
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_specific_password",
       use_ssl=True,
       port=993
   )

**Steps to get app-specific password:**

1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this password instead of your regular password

How do I connect to Outlook/Office 365?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient
   
   client = IMAPClient(
       host="outlook.office365.com",
       username="your_email@outlook.com",
       password="your_password",
       use_ssl=True,
       port=993
   )

Can I use OAuth2 authentication?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, Python Sage IMAP supports basic authentication (username/password). OAuth2 support is planned for future releases. For now, use app-specific passwords where required.

Usage and Operations
--------------------

How do I search for emails?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``IMAPSearchCriteria`` class for building search queries:

.. code-block:: python

   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.services import IMAPClient, IMAPMailboxService
   
   with IMAPClient(host="imap.gmail.com", username="user", password="pass") as client:
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Simple search
       criteria = IMAPSearchCriteria().from_address("sender@example.com")
       messages = mailbox.search(criteria)
       
       # Complex search
       criteria = (IMAPSearchCriteria()
                   .from_address("sender@example.com")
                   .subject("Important")
                   .since("2023-01-01")
                   .unseen())
       messages = mailbox.search(criteria)

How do I handle large mailboxes efficiently?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For large mailboxes, use these strategies:

1. **Use specific search criteria** to limit results:

   .. code-block:: python

      # Filter by date range
      criteria = IMAPSearchCriteria().since("2023-01-01").before("2023-12-31")

2. **Process in batches**:

   .. code-block:: python

      def process_in_batches(mailbox, criteria, batch_size=100):
          all_messages = mailbox.search(criteria)
          
          for i in range(0, len(all_messages), batch_size):
              batch = all_messages[i:i + batch_size]
              messages = mailbox.fetch(batch)
              
              for message in messages:
                  # Process each message
                  print(f"Subject: {message.subject}")

3. **Fetch only necessary fields**:

   .. code-block:: python

      # Only fetch headers
      messages = mailbox.fetch(message_set, fields=["ENVELOPE", "FLAGS"])

How do I download attachments?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   
   with IMAPClient(host="imap.gmail.com", username="user", password="pass") as client:
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Search for messages with attachments
       criteria = IMAPSearchCriteria().has_attachment()
       messages = mailbox.search(criteria)
       
       for message in messages:
           # Access attachments
           for attachment in message.attachments:
               print(f"Attachment: {attachment.filename}")
               
               # Save attachment
               with open(attachment.filename, 'wb') as f:
                   f.write(attachment.content)

How do I mark messages as read/unread?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.helpers.enums import MessageFlags
   
   # Mark as read
   mailbox.set_flags(message_set, [MessageFlags.SEEN])
   
   # Mark as unread (remove seen flag)
   mailbox.unset_flags(message_set, [MessageFlags.SEEN])
   
   # Mark as flagged/starred
   mailbox.set_flags(message_set, [MessageFlags.FLAGGED])

How do I move messages between folders?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Move messages to different folder
   mailbox.move_messages(message_set, "INBOX/Archive")
   
   # Copy messages (keep original)
   mailbox.copy_messages(message_set, "INBOX/Backup")

Performance and Optimization
----------------------------

How do I improve performance?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use connection pooling**:

   .. code-block:: python

      client = IMAPClient(
          host="imap.gmail.com",
          username="user",
          password="pass",
          max_connections=5,  # Enable connection pooling
          keepalive_interval=300.0
      )

2. **Enable monitoring** to track performance:

   .. code-block:: python

      client = IMAPClient(
          host="imap.gmail.com",
          username="user",
          password="pass",
          enable_monitoring=True
      )
      
      # Check metrics
      metrics = client.get_metrics()
      print(f"Average response time: {metrics.average_response_time}")

3. **Use specific search criteria** instead of fetching all messages
4. **Process in batches** for large datasets
5. **Fetch only required fields** to reduce data transfer

Why are my operations slow?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common causes and solutions:

1. **Network latency**: Use connection pooling and keepalive
2. **Large mailboxes**: Use specific search criteria and batch processing
3. **Fetching unnecessary data**: Specify only required fields
4. **Too many connections**: Limit concurrent connections
5. **Server-side limitations**: Check with your IMAP provider

How much memory will it use?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Memory usage depends on:

- **Number of messages processed**: Use batch processing for large sets
- **Message size**: Large attachments consume more memory
- **Connection pooling**: More connections = more memory
- **Fetched fields**: Minimize fields to reduce memory usage

For typical usage (processing hundreds of messages), expect 10-50MB of memory usage.

Error Handling and Troubleshooting
----------------------------------

What should I do if authentication fails?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Check credentials**: Verify username and password
2. **Use app-specific passwords**: Required for Gmail and many providers
3. **Check account security**: Ensure 2FA is configured correctly
4. **Test with simple email client**: Verify credentials work elsewhere
5. **Check provider documentation**: Some providers have specific requirements

See :ref:`troubleshooting` for detailed solutions.

How do I handle connection timeouts?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient
   from sage_imap.exceptions import IMAPConnectionError
   
   try:
       client = IMAPClient(
           host="imap.gmail.com",
           username="user",
           password="pass",
           timeout=60.0,  # Increase timeout
           max_retries=3,  # Enable retries
           retry_delay=1.0
       )
   except IMAPConnectionError as e:
       print(f"Connection failed: {e}")
       # Implement fallback logic

What exceptions should I handle?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Common exceptions to handle:

.. code-block:: python

   from sage_imap.exceptions import (
       IMAPConnectionError,
       IMAPAuthenticationError,
       IMAPSearchError,
       IMAPMessageError,
       IMAPFolderError
   )
   
   try:
       # IMAP operations
       pass
   except IMAPConnectionError:
       # Handle connection issues
       pass
   except IMAPAuthenticationError:
       # Handle authentication failures
       pass
   except IMAPSearchError:
       # Handle search failures
       pass
   except Exception as e:
       # Handle unexpected errors
       print(f"Unexpected error: {e}")

Development and Contributing
----------------------------

How can I contribute to the project?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We welcome contributions! See :ref:`contributing` for detailed guidelines.

Ways to contribute:

- **Report bugs**: Use GitHub issues
- **Suggest features**: Create feature requests
- **Submit code**: Fork, develop, and submit pull requests
- **Improve documentation**: Help improve these docs
- **Share examples**: Show how you use the library

How do I run tests?
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install development dependencies
   pip install -e ".[dev]"
   
   # Run tests
   pytest
   
   # Run with coverage
   pytest --cov=sage_imap

How do I build documentation locally?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Navigate to docs directory
   cd docs
   
   # Build documentation
   make html
   
   # On Windows
   make.bat html
   
   # Open in browser
   open _build/html/index.html

Is there a roadmap for future features?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes! Planned features include:

- OAuth2 authentication support
- Async/await support
- Enhanced attachment handling
- Message encryption/decryption
- Advanced folder synchronization
- Performance optimizations

Check our `GitHub issues <https://github.com/sageteamorg/python-sage-imap/issues>`_ for the latest roadmap.

Need More Help?
---------------

If you can't find the answer to your question here:

1. **Check the troubleshooting guide**: :ref:`troubleshooting`
2. **Look at examples**: :doc:`getting_started/examples/index`
3. **Search GitHub issues**: `Issues <https://github.com/sageteamorg/python-sage-imap/issues>`_
4. **Ask in discussions**: `Discussions <https://github.com/sageteamorg/python-sage-imap/discussions>`_
5. **Report bugs**: `New Issue <https://github.com/sageteamorg/python-sage-imap/issues/new>`_

**When asking for help, please include:**

- Python version
- Package version
- Error messages (full traceback)
- Minimal code example
- IMAP server details (Gmail, Outlook, etc.) 