.. _best_practices:

Best Practices
==============

This guide covers essential best practices for using Python Sage IMAP in production environments. Following these practices will help you build robust, scalable, and maintainable email processing applications.

Connection Management
---------------------

Use Context Managers
~~~~~~~~~~~~~~~~~~~~

Always use context managers for automatic resource management:

.. code-block:: python

   # ✅ Good - Automatic cleanup
   with IMAPClient(host="imap.example.com", username="user@example.com", password="password") as client:
       mailbox = IMAPMailboxService(client)
       # Operations here
   # Connection automatically closed

   # ❌ Bad - Manual cleanup required
   client = IMAPClient(host="imap.example.com", username="user@example.com", password="password")
   try:
       client.connect()
       # Operations here
   finally:
       client.disconnect()  # Easy to forget!

Configure Connection Pooling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For applications with multiple connections, use connection pooling:

.. code-block:: python

   from sage_imap.services.client import ConnectionConfig
   
   config = ConnectionConfig(
       host="imap.example.com",
       username="user@example.com",
       password="password",
       max_connections=5,          # Pool size
       keepalive_interval=300.0,   # 5 minutes
       timeout=30.0,               # 30 seconds
       enable_monitoring=True
   )
   
   # Use the same config for all connections
   with IMAPClient(config=config) as client:
       # Connection comes from pool
       pass

Set Appropriate Timeouts
~~~~~~~~~~~~~~~~~~~~~~~~~

Configure timeouts based on your network and server characteristics:

.. code-block:: python

   config = ConnectionConfig(
       host="imap.example.com",
       username="user@example.com",
       password="password",
       timeout=30.0,               # Connection timeout
       max_retries=3,              # Retry attempts
       retry_delay=1.0,            # Initial delay
       retry_exponential_backoff=True,  # Smart backoff
       max_retry_delay=30.0        # Maximum delay
   )

Error Handling
--------------

Handle Specific Exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Catch and handle specific exceptions appropriately:

.. code-block:: python

   from sage_imap.exceptions import (
       IMAPConnectionError,
       IMAPAuthenticationError,
       IMAPSearchError,
       IMAPMessageError
   )
   
   try:
       with IMAPClient(host="imap.example.com", username="user@example.com", password="password") as client:
           # Operations here
           pass
   except IMAPConnectionError as e:
       logger.error(f"Connection failed: {e}")
       # Implement retry logic or use backup server
   except IMAPAuthenticationError as e:
       logger.error(f"Authentication failed: {e}")
       # Check credentials, handle 2FA, etc.
   except IMAPSearchError as e:
       logger.error(f"Search failed: {e}")
       # Simplify search criteria or retry
   except IMAPMessageError as e:
       logger.error(f"Message operation failed: {e}")
       # Handle message-specific errors
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       # Handle unexpected errors gracefully

Implement Retry Logic
~~~~~~~~~~~~~~~~~~~~~

For transient errors, implement intelligent retry logic:

.. code-block:: python

   import time
   from random import uniform
   
   def with_retry(func, max_attempts=3, base_delay=1.0):
       """Execute function with exponential backoff retry."""
       for attempt in range(max_attempts):
           try:
               return func()
           except (IMAPConnectionError, IMAPMessageError) as e:
               if attempt == max_attempts - 1:
                   raise
               
               # Exponential backoff with jitter
               delay = base_delay * (2 ** attempt) + uniform(0, 1)
               logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
               time.sleep(delay)
   
   # Usage
   def search_emails():
       with IMAPClient(host="imap.example.com", username="user@example.com", password="password") as client:
           mailbox = IMAPMailboxService(client)
           return mailbox.search(IMAPSearchCriteria().unseen())
   
   messages = with_retry(search_emails)

Performance Optimization
------------------------

Use Efficient Search Criteria
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Optimize search operations for better performance:

.. code-block:: python

   from sage_imap.helpers.search import IMAPSearchCriteria
   
   # ✅ Good - Server-side filtering
   criteria = (IMAPSearchCriteria()
              .since("01-Jan-2024")
              .from_address("important@example.com")
              .unseen())
   
   # ❌ Bad - Fetching all then filtering
   all_messages = mailbox.search(IMAPSearchCriteria().all())
   filtered = [msg for msg in all_messages if msg.sender == "important@example.com"]

Batch Operations
~~~~~~~~~~~~~~~~

Process messages in batches for better performance:

.. code-block:: python

   from sage_imap.models.message import MessageSet
   
   def process_messages_in_batches(mailbox, message_uids, batch_size=100):
       """Process messages in batches for better performance."""
       for i in range(0, len(message_uids), batch_size):
           batch = message_uids[i:i + batch_size]
           message_set = MessageSet(batch)
           
           # Fetch batch
           messages = mailbox.fetch(message_set)
           
           # Process batch
           for message in messages:
               process_single_message(message)
           
           # Optional: brief pause between batches
           time.sleep(0.1)

Fetch Only Required Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Minimize data transfer by fetching only necessary fields:

.. code-block:: python

   # ✅ Good - Fetch only headers for initial processing
   messages = mailbox.fetch(
       message_set, 
       fields=["ENVELOPE", "FLAGS", "INTERNALDATE"]
   )
   
   # Only fetch full body when needed
   if needs_full_content:
       full_messages = mailbox.fetch(message_set, fields=["BODY"])

Security Best Practices
-----------------------

Secure Credential Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Never hardcode credentials in your application:

.. code-block:: python

   import os
   from sage_imap.services.client import ConnectionConfig
   
   # ✅ Good - Use environment variables
   config = ConnectionConfig(
       host=os.getenv("IMAP_HOST", "imap.example.com"),
       username=os.getenv("IMAP_USERNAME"),
       password=os.getenv("IMAP_PASSWORD"),
       use_ssl=True,
       port=993
   )
   
   # Or use a secure configuration management system
   from your_config_manager import get_secure_config
   
   config = get_secure_config("imap_settings")

Always Use SSL/TLS
~~~~~~~~~~~~~~~~~~

Ensure all connections use encryption:

.. code-block:: python

   # ✅ Good - Secure connection
   config = ConnectionConfig(
       host="imap.example.com",
       username="user@example.com",
       password="password",
       use_ssl=True,    # Always enable SSL
       port=993         # Standard SSL port
   )
   
   # ❌ Bad - Unencrypted connection
   config = ConnectionConfig(
       host="imap.example.com",
       username="user@example.com",
       password="password",
       use_ssl=False,   # Insecure!
       port=143
   )

Validate Server Certificates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For production environments, ensure proper certificate validation:

.. code-block:: python

   # Python Sage IMAP uses secure defaults
   # Certificate validation is enabled by default
   
   # For custom certificate validation, you can extend the client
   # (Advanced use case - contact support for guidance)

Logging and Monitoring
----------------------

Implement Comprehensive Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use structured logging for better debugging:

.. code-block:: python

   import logging
   import json
   from datetime import datetime
   
   # Configure structured logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   logger = logging.getLogger(__name__)
   
   class IMAPProcessor:
       def __init__(self, config):
           self.config = config
           self.client = IMAPClient(config=config)
       
       def process_messages(self):
           """Process messages with comprehensive logging."""
           start_time = datetime.now()
           
           try:
               with self.client:
                   logger.info("IMAP connection established", extra={
                       "host": self.config.host,
                       "username": self.config.username,
                       "timestamp": start_time.isoformat()
                   })
                   
                   mailbox = IMAPMailboxService(self.client)
                   mailbox.select("INBOX")
                   
                   # Search for messages
                   criteria = IMAPSearchCriteria().unseen()
                   message_uids = mailbox.search(criteria)
                   
                   logger.info(f"Found {len(message_uids)} unread messages")
                   
                   # Process messages
                   for uid in message_uids:
                       try:
                           message = mailbox.fetch(MessageSet([uid]))[0]
                           self.process_single_message(message)
                           
                           logger.debug(f"Processed message {uid}", extra={
                               "message_id": uid,
                               "subject": message.subject,
                               "sender": message.sender
                           })
                           
                       except Exception as e:
                           logger.error(f"Failed to process message {uid}: {e}")
                   
                   duration = datetime.now() - start_time
                   logger.info(f"Processing completed in {duration.total_seconds():.2f}s")
                   
           except Exception as e:
               logger.error(f"IMAP processing failed: {e}", exc_info=True)
               raise

Enable Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use built-in monitoring for performance insights:

.. code-block:: python

   config = ConnectionConfig(
       host="imap.example.com",
       username="user@example.com",
       password="password",
       enable_monitoring=True
   )
   
   with IMAPClient(config=config) as client:
       # Your operations here
       
       # Get performance metrics
       metrics = client.get_metrics()
       
       # Log performance data
       logger.info("Performance metrics", extra={
           "connection_attempts": metrics.connection_attempts,
           "successful_connections": metrics.successful_connections,
           "failed_connections": metrics.failed_connections,
           "average_response_time": metrics.average_response_time,
           "total_operations": metrics.total_operations,
           "failed_operations": metrics.failed_operations
       })

Application Architecture
------------------------

Use Dependency Injection
~~~~~~~~~~~~~~~~~~~~~~~~~

Make your application testable and configurable:

.. code-block:: python

   from abc import ABC, abstractmethod
   
   class EmailProcessor(ABC):
       @abstractmethod
       def process_emails(self):
           pass
   
   class IMAPEmailProcessor(EmailProcessor):
       def __init__(self, config: ConnectionConfig):
           self.config = config
       
       def process_emails(self):
           with IMAPClient(config=self.config) as client:
               # Implementation here
               pass
   
   # Usage
   def create_email_processor(config_name: str) -> EmailProcessor:
       config = load_config(config_name)
       return IMAPEmailProcessor(config)
   
   # Easy to test and swap implementations
   processor = create_email_processor("production")
   processor.process_emails()

Implement Circuit Breaker Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For resilient applications, implement circuit breaker pattern:

.. code-block:: python

   import time
   from enum import Enum
   
   class CircuitState(Enum):
       CLOSED = "closed"
       OPEN = "open"
       HALF_OPEN = "half_open"
   
   class CircuitBreaker:
       def __init__(self, failure_threshold=5, recovery_timeout=60):
           self.failure_threshold = failure_threshold
           self.recovery_timeout = recovery_timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = CircuitState.CLOSED
       
       def call(self, func, *args, **kwargs):
           if self.state == CircuitState.OPEN:
               if time.time() - self.last_failure_time > self.recovery_timeout:
                   self.state = CircuitState.HALF_OPEN
               else:
                   raise Exception("Circuit breaker is OPEN")
           
           try:
               result = func(*args, **kwargs)
               self.on_success()
               return result
           except Exception as e:
               self.on_failure()
               raise
       
       def on_success(self):
           self.failure_count = 0
           self.state = CircuitState.CLOSED
       
       def on_failure(self):
           self.failure_count += 1
           self.last_failure_time = time.time()
           
           if self.failure_count >= self.failure_threshold:
               self.state = CircuitState.OPEN
   
   # Usage
   circuit_breaker = CircuitBreaker()
   
   def process_emails_with_circuit_breaker():
       return circuit_breaker.call(process_emails)

Testing Best Practices
-----------------------

Mock External Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use mocks for unit testing:

.. code-block:: python

   import unittest
   from unittest.mock import Mock, patch
   
   class TestIMAPProcessor(unittest.TestCase):
       def setUp(self):
           self.config = ConnectionConfig(
               host="test.example.com",
               username="test@example.com",
               password="test_password"
           )
       
       @patch('sage_imap.services.client.IMAPClient')
       def test_process_messages(self, mock_client):
           # Mock the client
           mock_client_instance = Mock()
           mock_client.return_value.__enter__.return_value = mock_client_instance
           
           # Mock mailbox service
           mock_mailbox = Mock()
           mock_mailbox.search.return_value = [1, 2, 3]
           
           # Test your processor
           processor = IMAPProcessor(self.config)
           processor.process_messages()
           
           # Verify interactions
           mock_client.assert_called_once_with(config=self.config)
           mock_mailbox.search.assert_called_once()

Integration Testing
~~~~~~~~~~~~~~~~~~~

Test with real IMAP servers in staging:

.. code-block:: python

   import pytest
   
   @pytest.mark.integration
   def test_real_imap_connection():
       """Integration test with real IMAP server."""
       config = ConnectionConfig(
           host=os.getenv("TEST_IMAP_HOST"),
           username=os.getenv("TEST_IMAP_USERNAME"),
           password=os.getenv("TEST_IMAP_PASSWORD"),
           timeout=10.0
       )
       
       with IMAPClient(config=config) as client:
           mailbox = IMAPMailboxService(client)
           folders = mailbox.list_folders()
           
           assert "INBOX" in folders
           assert isinstance(folders, list)

Deployment Considerations
-------------------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

Use configuration files for different environments:

.. code-block:: python

   import yaml
   from dataclasses import dataclass
   
   @dataclass
   class IMAPConfig:
       host: str
       username: str
       password: str
       port: int = 993
       use_ssl: bool = True
       timeout: float = 30.0
       max_retries: int = 3
       enable_monitoring: bool = True
   
   def load_config(env: str) -> IMAPConfig:
       """Load configuration for specific environment."""
       with open(f"config/{env}.yaml", 'r') as f:
           config_data = yaml.safe_load(f)
       
       return IMAPConfig(**config_data['imap'])
   
   # Usage
   config = load_config("production")
   imap_config = ConnectionConfig(**config.__dict__)

Health Checks
~~~~~~~~~~~~~

Implement health check endpoints for monitoring:

.. code-block:: python

   from flask import Flask, jsonify
   
   app = Flask(__name__)
   
   @app.route('/health/imap')
   def imap_health_check():
       """Health check endpoint for IMAP connectivity."""
       try:
           config = load_config("production")
           
           with IMAPClient(config=config) as client:
               # Quick connection test
               capabilities = client.capabilities
               
               return jsonify({
                   "status": "healthy",
                   "capabilities": capabilities,
                   "timestamp": datetime.now().isoformat()
               })
               
       except Exception as e:
           return jsonify({
               "status": "unhealthy",
               "error": str(e),
               "timestamp": datetime.now().isoformat()
           }), 500

Graceful Shutdown
~~~~~~~~~~~~~~~~~

Implement graceful shutdown for long-running processes:

.. code-block:: python

   import signal
   import threading
   
   class IMAPService:
       def __init__(self, config):
           self.config = config
           self.running = True
           self.current_client = None
       
       def stop(self):
           """Stop the service gracefully."""
           self.running = False
           if self.current_client:
               try:
                   self.current_client.disconnect()
               except:
                   pass
       
       def run(self):
           """Main service loop."""
           while self.running:
               try:
                   with IMAPClient(config=self.config) as client:
                       self.current_client = client
                       
                       # Process messages
                       self.process_messages(client)
                       
               except Exception as e:
                   logger.error(f"Service error: {e}")
                   if self.running:
                       time.sleep(5)  # Wait before retry
               
               time.sleep(1)  # Brief pause between cycles
   
   # Usage
   service = IMAPService(config)
   
   def signal_handler(signum, frame):
       logger.info("Shutdown signal received")
       service.stop()
   
   signal.signal(signal.SIGINT, signal_handler)
   signal.signal(signal.SIGTERM, signal_handler)
   
   service.run()

Summary
-------

Key takeaways for production use:

1. **Always use context managers** for resource management
2. **Implement comprehensive error handling** with specific exceptions
3. **Use connection pooling** for multiple connections
4. **Optimize search criteria** for better performance
5. **Process messages in batches** for large volumes
6. **Secure credential management** with environment variables
7. **Enable monitoring** for performance insights
8. **Implement proper logging** with structured data
9. **Use circuit breaker pattern** for resilience
10. **Test thoroughly** with both unit and integration tests

Following these best practices will help you build robust, scalable, and maintainable email processing applications with Python Sage IMAP. 