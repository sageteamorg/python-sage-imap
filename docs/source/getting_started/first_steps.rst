.. _first_steps:

First Steps
===========

This guide will walk you through your first Python Sage IMAP connection and basic operations. By the end of this tutorial, you'll have a working IMAP client that can connect to a server, browse folders, and read emails.

Prerequisites
-------------

Before starting, make sure you have:

1. **Python 3.7+** installed on your system
2. **Python Sage IMAP** installed (see :doc:`installation`)
3. **IMAP server credentials** (host, username, password)
4. **Network access** to your IMAP server

Your First Connection
---------------------

Let's start with a simple connection example:

.. code-block:: python

   from sage_imap.services import IMAPClient
   from sage_imap.exceptions import IMAPConnectionError, IMAPAuthenticationError
   
   # Replace with your actual IMAP server details
   HOST = "imap.example.com"
   USERNAME = "john.doe@example.com"
   PASSWORD = "your_secure_password"
   
   try:
       # Create and connect to IMAP server
       with IMAPClient(host=HOST, username=USERNAME, password=PASSWORD) as client:
           print("✓ Successfully connected to IMAP server!")
           print(f"Server capabilities: {client.capabilities}")
           
   except IMAPConnectionError as e:
       print(f"✗ Connection failed: {e}")
   except IMAPAuthenticationError as e:
       print(f"✗ Authentication failed: {e}")

Understanding the Code
~~~~~~~~~~~~~~~~~~~~~~

Let's break down what's happening:

1. **Import statements**: We import the necessary classes and exceptions
2. **Connection details**: Set your IMAP server credentials
3. **Context manager**: Use ``with`` statement for automatic resource management
4. **Error handling**: Catch specific exceptions for better debugging

Connection Configuration
------------------------

For more control over your connection, you can use ``ConnectionConfig``:

.. code-block:: python

   from sage_imap.services import IMAPClient
   from sage_imap.services.client import ConnectionConfig
   
   # Create a configuration object
   config = ConnectionConfig(
       host="imap.example.com",
       username="john.doe@example.com",
       password="your_secure_password",
       port=993,                    # Standard IMAP SSL port
       use_ssl=True,               # Enable SSL/TLS
       timeout=30.0,               # Connection timeout in seconds
       max_retries=3,              # Number of retry attempts
       retry_delay=1.0,            # Initial delay between retries
       enable_monitoring=True      # Enable connection monitoring
   )
   
   # Create client with configuration
   client = IMAPClient(config=config)
   
   try:
       client.connect()
       print("✓ Connected with custom configuration!")
       
       # Check connection metrics
       if config.enable_monitoring:
           metrics = client.get_metrics()
           print(f"Connection attempts: {metrics.connection_attempts}")
           print(f"Response time: {metrics.average_response_time:.2f}s")
           
   except Exception as e:
       print(f"✗ Connection failed: {e}")
   finally:
       client.disconnect()

Working with Mailboxes
-----------------------

Once connected, you can work with mailboxes (folders):

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   
   with IMAPClient(host="imap.example.com", username="john.doe@example.com", password="your_secure_password") as client:
       # Create mailbox service
       mailbox = IMAPMailboxService(client)
       
       # List available folders
       folders = mailbox.list_folders()
       print("Available folders:")
       for folder in folders:
           print(f"  - {folder}")
       
       # Select INBOX
       mailbox.select("INBOX")
       print("✓ INBOX selected")
       
       # Get mailbox status
       status = mailbox.get_status()
       print(f"Messages in INBOX: {status.get('MESSAGES', 0)}")
       print(f"Unread messages: {status.get('UNSEEN', 0)}")

Searching for Messages
----------------------

Let's search for some emails:

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   from sage_imap.helpers.search import IMAPSearchCriteria
   
   with IMAPClient(host="imap.example.com", username="john.doe@example.com", password="your_secure_password") as client:
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Search for all messages
       all_criteria = IMAPSearchCriteria().all()
       all_messages = mailbox.search(all_criteria)
       print(f"Total messages: {len(all_messages)}")
       
       # Search for unread messages
       unread_criteria = IMAPSearchCriteria().unseen()
       unread_messages = mailbox.search(unread_criteria)
       print(f"Unread messages: {len(unread_messages)}")
       
       # Search for messages from specific sender
       sender_criteria = IMAPSearchCriteria().from_address("notifications@example.com")
       sender_messages = mailbox.search(sender_criteria)
       print(f"Messages from notifications@example.com: {len(sender_messages)}")
       
       # Complex search: unread messages from today
       from datetime import datetime
       today = datetime.now().strftime("%d-%b-%Y")
       
       complex_criteria = (IMAPSearchCriteria()
                          .unseen()
                          .since(today))
       today_unread = mailbox.search(complex_criteria)
       print(f"Unread messages from today: {len(today_unread)}")

Reading Messages
----------------

Now let's read some actual message content:

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   
   with IMAPClient(host="imap.example.com", username="john.doe@example.com", password="your_secure_password") as client:
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Get recent messages
       recent_criteria = IMAPSearchCriteria().recent()
       message_ids = mailbox.search(recent_criteria)
       
       if message_ids:
           # Take first 5 messages
           first_five = MessageSet(message_ids[:5])
           
           # Fetch message details
           messages = mailbox.fetch(first_five)
           
           print("Recent messages:")
           for message in messages:
               print(f"  Subject: {message.subject}")
               print(f"  From: {message.sender}")
               print(f"  Date: {message.date}")
               print(f"  Read: {'Yes' if message.seen else 'No'}")
               print("-" * 50)

Working with Message Flags
---------------------------

You can manage message flags (read/unread, flagged, etc.):

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.helpers.enums import MessageFlags
   from sage_imap.models.message import MessageSet
   
   with IMAPClient(host="imap.example.com", username="john.doe@example.com", password="your_secure_password") as client:
       mailbox = IMAPMailboxService(client)
       mailbox.select("INBOX")
       
       # Find unread messages
       unread_criteria = IMAPSearchCriteria().unseen()
       unread_ids = mailbox.search(unread_criteria)
       
       if unread_ids:
           # Take first message
           first_message = MessageSet([unread_ids[0]])
           
           # Mark as read
           mailbox.set_flags(first_message, [MessageFlags.SEEN])
           print("✓ Message marked as read")
           
           # Add important flag
           mailbox.set_flags(first_message, [MessageFlags.FLAGGED])
           print("✓ Message marked as important")
           
           # Remove important flag
           mailbox.unset_flags(first_message, [MessageFlags.FLAGGED])
           print("✓ Important flag removed")

Error Handling Best Practices
------------------------------

Always include proper error handling:

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   from sage_imap.exceptions import (
       IMAPConnectionError,
       IMAPAuthenticationError,
       IMAPSearchError,
       IMAPMessageError
   )
   
   def safe_imap_operation():
       try:
           with IMAPClient(host="imap.example.com", username="john.doe@example.com", password="your_secure_password") as client:
               mailbox = IMAPMailboxService(client)
               mailbox.select("INBOX")
               
               # Your operations here
               messages = mailbox.search(IMAPSearchCriteria().all())
               print(f"Found {len(messages)} messages")
               
       except IMAPConnectionError as e:
           print(f"Connection error: {e}")
           print("Check your network connection and server details")
           
       except IMAPAuthenticationError as e:
           print(f"Authentication error: {e}")
           print("Check your username and password")
           
       except IMAPSearchError as e:
           print(f"Search error: {e}")
           print("Check your search criteria")
           
       except IMAPMessageError as e:
           print(f"Message operation error: {e}")
           
       except Exception as e:
           print(f"Unexpected error: {e}")
   
   # Call the function
   safe_imap_operation()

Common Configuration Examples
-----------------------------

Gmail Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient
   
   # Gmail requires app-specific password
   gmail_client = IMAPClient(
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_specific_password",  # Not your regular password!
       port=993,
       use_ssl=True
   )

Outlook/Office 365 Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient
   
   outlook_client = IMAPClient(
       host="outlook.office365.com",
       username="your_email@outlook.com",
       password="your_password",
       port=993,
       use_ssl=True
   )

Custom Server Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient
   
   custom_client = IMAPClient(
       host="mail.yourcompany.com",
       username="your_username",
       password="your_password",
       port=993,                    # Or 143 for non-SSL
       use_ssl=True,               # False for non-SSL
       timeout=60.0,               # Longer timeout for slow servers
       max_retries=5               # More retries for unstable connections
   )

Next Steps
----------

Congratulations! You've successfully:

- ✅ Connected to an IMAP server
- ✅ Listed mailbox folders
- ✅ Searched for messages
- ✅ Read message content
- ✅ Managed message flags
- ✅ Implemented error handling

Ready to learn more? Here's what to explore next:

**Core Concepts**:
   - :doc:`terminologies` - Understanding IMAP terminology
   - :doc:`features` - Complete feature overview
   - :doc:`search` - Advanced search capabilities

**Advanced Topics**:
   - :doc:`message_set` - Working with message collections
   - :doc:`headers` - Email header manipulation
   - :doc:`best_practices` - Production best practices

**Reference**:
   - :doc:`../faq` - Frequently asked questions
   - :doc:`../troubleshooting` - Common issues and solutions

Tips for Success
-----------------

1. **Start Simple**: Begin with basic operations before moving to complex ones
2. **Use Context Managers**: Always use ``with`` statements for automatic cleanup
3. **Handle Errors**: Include proper exception handling in your code
4. **Monitor Performance**: Enable monitoring for production applications
5. **Test Thoroughly**: Test with your specific IMAP server configuration
6. **Read Documentation**: Explore the comprehensive documentation for advanced features

**Happy coding with Python Sage IMAP!** 🚀 