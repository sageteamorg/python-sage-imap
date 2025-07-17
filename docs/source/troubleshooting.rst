.. _troubleshooting:

Troubleshooting
===============

This section covers common issues and their solutions when using Python Sage IMAP.

Connection Issues
-----------------

Connection Timeout
~~~~~~~~~~~~~~~~~~

**Problem**: Connection to IMAP server times out.

**Common Causes**:

- Network connectivity issues

- Firewall blocking connections

- Server-side rate limiting

- Incorrect host or port settings

**Solutions**:

1. **Check network connectivity**:

   .. code-block:: python

      import socket
      
      def test_connection(host, port):
          try:
              socket.create_connection((host, port), timeout=10)
              print(f"Connection to {host}:{port} successful")
              return True
          except socket.error as e:
              print(f"Connection failed: {e}")
              return False
      
      # Test connection
      test_connection("imap.gmail.com", 993)

2. **Increase timeout**:

   .. code-block:: python

      from sage_imap.services import IMAPClient
      
      # Increase timeout to 60 seconds
      client = IMAPClient(
          host="imap.gmail.com",
          username="your_email@gmail.com",
          password="your_password",
          timeout=60.0
      )

3. **Check firewall settings**:

   - Ensure ports 993 (SSL) or 143 (non-SSL) are open

   - Check corporate firewall settings

   - Verify proxy settings if applicable

SSL/TLS Issues
~~~~~~~~~~~~~~

**Problem**: SSL certificate verification fails.

**Symptoms**:

- ``ssl.SSLError`` exceptions

- Certificate verification errors

- Connection refused errors

**Solutions**:

1. **Verify SSL settings**:

   .. code-block:: python

      # For development/testing only - not recommended for production
      import ssl
      from sage_imap.services import IMAPClient
      
      # Create SSL context with reduced verification
      ssl_context = ssl.create_default_context()
      ssl_context.check_hostname = False
      ssl_context.verify_mode = ssl.CERT_NONE
      
      # Note: This approach requires custom implementation

2. **Check certificate validity**:

   .. code-block:: bash

      # Check certificate expiration
      openssl s_client -connect imap.gmail.com:993 -servername imap.gmail.com

3. **Use correct SSL configuration**:

   .. code-block:: python

      from sage_imap.services import IMAPClient
      
      # Ensure SSL is enabled for secure connections
      client = IMAPClient(
          host="imap.gmail.com",
          username="your_email@gmail.com",
          password="your_password",
          use_ssl=True,
          port=993
      )

Authentication Problems
-----------------------

Invalid Credentials
~~~~~~~~~~~~~~~~~~~

**Problem**: Authentication fails with correct credentials.

**Common Causes**:
- App-specific passwords required
- Two-factor authentication enabled
- Account security settings
- OAuth2 required instead of basic auth

**Solutions**:

1. **Gmail Users**: Enable app-specific passwords

   .. code-block:: python

      from sage_imap.services import IMAPClient
      
      # Use app-specific password instead of regular password
      client = IMAPClient(
          host="imap.gmail.com",
          username="your_email@gmail.com",
          password="your_app_specific_password",  # Not your regular password
          use_ssl=True
      )

2. **Check account security settings**:
   - Enable "Less secure app access" if required
   - Verify two-factor authentication configuration
   - Check for account locks or restrictions

3. **Test with different authentication methods**:

   .. code-block:: python

      from sage_imap.services import IMAPClient
      
      # Try different authentication approaches
      try:
          client = IMAPClient(
              host="imap.gmail.com",
              username="your_email@gmail.com",
              password="your_password"
          )
          with client:
              print("Authentication successful")
      except Exception as e:
          print(f"Authentication failed: {e}")

Search and Query Issues
-----------------------

Empty Search Results
~~~~~~~~~~~~~~~~~~~~

**Problem**: Search queries return no results despite expecting matches.

**Debugging Steps**:

1. **Verify search criteria**:

   .. code-block:: python

      from sage_imap.helpers.search import IMAPSearchCriteria
      from sage_imap.services import IMAPClient, IMAPMailboxService
      
      with IMAPClient(host="imap.gmail.com", username="user@gmail.com", password="password") as client:
          mailbox = IMAPMailboxService(client)
          mailbox.select("INBOX")
          
          # Debug search with simple criteria first
          criteria = IMAPSearchCriteria().all()
          all_messages = mailbox.search(criteria)
          print(f"Total messages in INBOX: {len(all_messages)}")
          
          # Then try specific criteria
          criteria = IMAPSearchCriteria().from_address("sender@example.com")
          filtered_messages = mailbox.search(criteria)
          print(f"Messages from sender: {len(filtered_messages)}")

2. **Check folder selection**:

   .. code-block:: python

      # List all folders to ensure correct folder selection
      folders = client.list_folders()
      print("Available folders:", folders)
      
      # Select the correct folder
      mailbox.select("INBOX")  # or another folder

3. **Test search criteria independently**:

   .. code-block:: python

      from sage_imap.helpers.search import IMAPSearchCriteria
      
      # Test each criterion separately
      criteria1 = IMAPSearchCriteria().from_address("sender@example.com")
      criteria2 = IMAPSearchCriteria().subject("Test Subject")
      criteria3 = IMAPSearchCriteria().unseen()
      
      results1 = mailbox.search(criteria1)
      results2 = mailbox.search(criteria2)
      results3 = mailbox.search(criteria3)

Performance Issues
------------------

Slow Operations
~~~~~~~~~~~~~~~

**Problem**: IMAP operations are slow or hang.

**Optimization Strategies**:

1. **Use connection pooling**:

   .. code-block:: python

      from sage_imap.services import IMAPClient
      
      # Enable connection pooling for better performance
      client = IMAPClient(
          host="imap.gmail.com",
          username="your_email@gmail.com",
          password="your_password",
          max_connections=5,  # Adjust based on needs
          keepalive_interval=300.0
      )

2. **Optimize fetch operations**:

   .. code-block:: python

      # Fetch only necessary fields
      messages = mailbox.fetch(
          message_set,
          fields=["ENVELOPE", "FLAGS"],  # Only fetch required fields
          batch_size=50  # Process in smaller batches
      )

3. **Use efficient search criteria**:

   .. code-block:: python

      from sage_imap.helpers.search import IMAPSearchCriteria
      
      # More efficient: use server-side filtering
      criteria = IMAPSearchCriteria().since("2023-01-01").from_address("sender@example.com")
      
      # Less efficient: fetch all then filter client-side
      # Don't do this for large mailboxes

Memory Issues
~~~~~~~~~~~~~

**Problem**: High memory usage when processing large mailboxes.

**Solutions**:

1. **Process messages in batches**:

   .. code-block:: python

      def process_messages_in_batches(mailbox, criteria, batch_size=100):
          all_messages = mailbox.search(criteria)
          
          for i in range(0, len(all_messages), batch_size):
              batch = all_messages[i:i + batch_size]
              messages = mailbox.fetch(batch)
              
              # Process batch
              for message in messages:
                  process_message(message)
              
              # Optional: garbage collection
              import gc
              gc.collect()

2. **Use generators for large datasets**:

   .. code-block:: python

      def message_generator(mailbox, criteria, batch_size=100):
          all_messages = mailbox.search(criteria)
          
          for i in range(0, len(all_messages), batch_size):
              batch = all_messages[i:i + batch_size]
              messages = mailbox.fetch(batch)
              
              for message in messages:
                  yield message

3. **Limit fetch fields**:

   .. code-block:: python

      # Only fetch headers for initial processing
      messages = mailbox.fetch(
          message_set,
          fields=["ENVELOPE", "FLAGS", "INTERNALDATE"]
      )

Error Handling
--------------

Common Exceptions
~~~~~~~~~~~~~~~~~

**IMAPConnectionError**:

.. code-block:: python

   from sage_imap.exceptions import IMAPConnectionError
   
   try:
       with IMAPClient(host="imap.example.com", username="user", password="pass") as client:
           # Operations
           pass
   except IMAPConnectionError as e:
       print(f"Connection failed: {e}")
       # Implement retry logic or fallback

**IMAPAuthenticationError**:

.. code-block:: python

   from sage_imap.exceptions import IMAPAuthenticationError
   
   try:
       client = IMAPClient(host="imap.gmail.com", username="user", password="pass")
       client.connect()
   except IMAPAuthenticationError as e:
       print(f"Authentication failed: {e}")
       # Check credentials, app passwords, etc.

**IMAPSearchError**:

.. code-block:: python

   from sage_imap.exceptions import IMAPSearchError
   
   try:
       results = mailbox.search(criteria)
   except IMAPSearchError as e:
       print(f"Search failed: {e}")
       # Simplify search criteria or check folder selection

Debugging Tips
--------------

Enable Logging
~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   
   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)
   logger = logging.getLogger('sage_imap')
   logger.setLevel(logging.DEBUG)
   
   # Now run your IMAP operations
   with IMAPClient(host="imap.gmail.com", username="user", password="pass") as client:
       # Debug information will be logged
       pass

Monitor Connection Health
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPClient
   
   client = IMAPClient(
       host="imap.gmail.com",
       username="user@gmail.com",
       password="password",
       enable_monitoring=True
   )
   
   with client:
       # Check connection metrics
       metrics = client.get_metrics()
       print(f"Connection attempts: {metrics.connection_attempts}")
       print(f"Failed connections: {metrics.failed_connections}")
       print(f"Average response time: {metrics.average_response_time}")

Test with Simple Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Start with basic operations to isolate issues
   def test_basic_operations():
       try:
           with IMAPClient(host="imap.gmail.com", username="user", password="pass") as client:
               # Test connection
               print("✓ Connection successful")
               
               # Test folder listing
               folders = client.list_folders()
               print(f"✓ Found {len(folders)} folders")
               
               # Test mailbox selection
               mailbox = IMAPMailboxService(client)
               mailbox.select("INBOX")
               print("✓ INBOX selected successfully")
               
               # Test simple search
               criteria = IMAPSearchCriteria().all()
               messages = mailbox.search(criteria)
               print(f"✓ Found {len(messages)} messages")
               
       except Exception as e:
           print(f"✗ Error: {e}")
           import traceback
           traceback.print_exc()

Getting Help
------------

When reporting issues, please include:

1. **Python version**: ``python --version``
2. **Package version**: ``pip show python-sage-imap``
3. **Error messages**: Full traceback
4. **Code sample**: Minimal example reproducing the issue
5. **IMAP server**: Provider (Gmail, Outlook, etc.)
6. **Operating system**: OS and version

**Community Support**:

- GitHub Issues: `Report bugs and feature requests <https://github.com/sageteamorg/python-sage-imap/issues>`_
- Discussions: `Ask questions and share tips <https://github.com/sageteamorg/python-sage-imap/discussions>`_
- Documentation: `Browse the full documentation <https://python-sage-imap.readthedocs.io/>`_

**Before Reporting**:

1. Check this troubleshooting guide
2. Search existing issues
3. Try the latest version
4. Test with minimal code example 