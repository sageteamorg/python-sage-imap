.. _basic_usage_example:

Basic Client Usage
==================

This example demonstrates the fundamental usage patterns of Python Sage IMAP using **UID-based operations** for reliability and the enhanced MessageSet capabilities.

**⚠️ IMPORTANT: This example uses UIDs throughout for production reliability!**

Overview
--------

You'll learn how to:

- Establish secure IMAP connections with proper configuration
- Use UID-based services for reliable operations
- Work with the enhanced MessageSet class
- Handle basic mailbox operations safely
- Implement proper error handling and logging
- Use context managers for resource management

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed (``pip install python-sage-imap``)
- Valid IMAP server credentials
- Understanding of UID vs sequence number concepts

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Basic IMAPClient Usage Example with UID-based Operations
   
   This example demonstrates modern usage patterns emphasizing UID-based operations
   for reliability and the enhanced MessageSet capabilities.
   """
   
   import logging
   import time
   from datetime import datetime
   from typing import Optional, List
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService, IMAPFolderService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.helpers.enums import MessagePart, Flag
   from sage_imap.exceptions import (
       IMAPConnectionError, 
       IMAPAuthenticationError,
       IMAPOperationError
   )
   
   # Configure logging to see detailed information
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class BasicIMAPExample:
       """
       Basic IMAP client example using UID-based operations.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the IMAP client with connection parameters.
           
           Args:
               host: IMAP server hostname
               username: Email account username
               password: Email account password
               port: IMAP server port (default 993 for SSL)
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
       def demonstrate_basic_operations(self):
           """
           Demonstrate basic IMAP operations using UID-based services.
           """
           logger.info("=== Basic IMAP Operations Example ===")
           
           try:
               # Use context manager for automatic resource cleanup
               with IMAPClient(config=self.config) as client:
                   
                   # Initialize UID-based service (recommended for production)
                   uid_service = IMAPMailboxUIDService(client)
                   folder_service = IMAPFolderService(client)
                   
                   # List available folders
                   self.demonstrate_folder_listing(folder_service)
                   
                   # Select INBOX for operations
                   uid_service.select("INBOX")
                   logger.info("✓ Selected INBOX mailbox")
                   
                   # Get mailbox status
                   self.demonstrate_mailbox_status(uid_service)
                   
                   # Search for emails using UID-based operations
                   self.demonstrate_uid_search(uid_service)
                   
                   # Fetch email content
                   self.demonstrate_email_fetching(uid_service)
                   
                   # Demonstrate MessageSet operations
                   self.demonstrate_message_set_usage(uid_service)
                   
                   logger.info("✓ Basic operations completed successfully")
                   
           except IMAPConnectionError as e:
               logger.error(f"Connection failed: {e}")
               raise
           except IMAPAuthenticationError as e:
               logger.error(f"Authentication failed: {e}")
               raise
           except IMAPOperationError as e:
               logger.error(f"IMAP operation failed: {e}")
               raise
           except Exception as e:
               logger.error(f"Unexpected error: {e}")
               raise
   
       def demonstrate_folder_listing(self, folder_service: IMAPFolderService):
           """
           Show how to list available folders.
           """
           logger.info("--- Listing Available Folders ---")
           
           try:
               folders = folder_service.list_folders()
               logger.info(f"Found {len(folders)} folders:")
               
               for folder in folders[:10]:  # Show first 10 folders
                   logger.info(f"  📁 {folder}")
                   
               if len(folders) > 10:
                   logger.info(f"  ... and {len(folders) - 10} more folders")
                   
           except Exception as e:
               logger.error(f"Failed to list folders: {e}")
   
       def demonstrate_mailbox_status(self, uid_service: IMAPMailboxUIDService):
           """
           Show how to get mailbox status information.
           """
           logger.info("--- Mailbox Status Information ---")
           
           try:
               # Get basic mailbox information
               status_result = uid_service.get_mailbox_status()
               
               if status_result.success:
                   status = status_result.metadata
                   logger.info(f"📊 Mailbox Status:")
                   logger.info(f"  • Total messages: {status.get('EXISTS', 'N/A')}")
                   logger.info(f"  • Recent messages: {status.get('RECENT', 'N/A')}")
                   logger.info(f"  • Unseen messages: {status.get('UNSEEN', 'N/A')}")
                   logger.info(f"  • Next UID: {status.get('UIDNEXT', 'N/A')}")
                   logger.info(f"  • UID validity: {status.get('UIDVALIDITY', 'N/A')}")
               else:
                   logger.error("Failed to get mailbox status")
                   
           except Exception as e:
               logger.error(f"Failed to get mailbox status: {e}")
   
       def demonstrate_uid_search(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate UID-based search operations.
           """
           logger.info("--- UID-Based Search Operations ---")
           
           try:
               # Search for recent emails (last 7 days)
               recent_criteria = IMAPSearchCriteria.since_days(7)
               recent_msg_set = uid_service.create_message_set_from_search(recent_criteria)
               
               logger.info(f"📧 Recent emails (last 7 days): {len(recent_msg_set)}")
               
               # Search for unread emails
               unread_criteria = IMAPSearchCriteria.UNSEEN
               unread_msg_set = uid_service.create_message_set_from_search(unread_criteria)
               
               logger.info(f"📧 Unread emails: {len(unread_msg_set)}")
               
               # Search for emails with attachments
               attachment_criteria = IMAPSearchCriteria.has_attachments()
               attachment_msg_set = uid_service.create_message_set_from_search(attachment_criteria)
               
               logger.info(f"📧 Emails with attachments: {len(attachment_msg_set)}")
               
               # Complex search: Unread emails from specific sender
               complex_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNSEEN,
                   IMAPSearchCriteria.from_address("@example.com")
               )
               complex_msg_set = uid_service.create_message_set_from_search(complex_criteria)
               
               logger.info(f"📧 Unread emails from @example.com: {len(complex_msg_set)}")
               
               # Store the recent messages for later use
               self.recent_messages = recent_msg_set
               
           except Exception as e:
               logger.error(f"Failed to perform UID search: {e}")
   
       def demonstrate_email_fetching(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate fetching email content using UIDs.
           """
           logger.info("--- Email Content Fetching ---")
           
           try:
               # Get recent messages (from previous search)
               if hasattr(self, 'recent_messages') and not self.recent_messages.is_empty():
                   # Take first 5 messages for demonstration
                   sample_uids = list(self.recent_messages.parsed_ids)[:5]
                   sample_msg_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
                   
                   logger.info(f"Fetching content for {len(sample_msg_set)} messages...")
                   
                   # Fetch message headers and basic info
                   fetch_result = uid_service.uid_fetch(sample_msg_set, MessagePart.HEADER)
                   
                   if fetch_result.success:
                       messages = fetch_result.metadata.get('fetched_messages', [])
                       
                       for i, message in enumerate(messages, 1):
                           logger.info(f"📄 Message {i}:")
                           logger.info(f"  • UID: {message.uid}")
                           logger.info(f"  • Subject: {message.subject}")
                           logger.info(f"  • From: {message.from_address}")
                           logger.info(f"  • Date: {message.date}")
                           logger.info(f"  • Size: {message.size} bytes")
                           logger.info(f"  • Has attachments: {message.has_attachments()}")
                           logger.info("")
                   else:
                       logger.error("Failed to fetch messages")
               else:
                   logger.info("No recent messages to fetch")
                   
           except Exception as e:
               logger.error(f"Failed to fetch email content: {e}")
   
       def demonstrate_message_set_usage(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate advanced MessageSet usage patterns.
           """
           logger.info("--- MessageSet Usage Patterns ---")
           
           try:
               # Create MessageSet from UIDs
               sample_uids = [1001, 1002, 1003, 1005, 1006, 1007, 1010]
               uid_msg_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"📋 Created MessageSet from UIDs: {uid_msg_set}")
               logger.info(f"  • Contains {len(uid_msg_set)} messages")
               logger.info(f"  • Optimized string: {uid_msg_set.optimized_string}")
               
               # Create MessageSet from range
               range_msg_set = MessageSet.from_range(1000, 1020, mailbox="INBOX")
               logger.info(f"📋 Created MessageSet from range: {range_msg_set}")
               
               # Demonstrate set operations
               if not uid_msg_set.is_empty() and not range_msg_set.is_empty():
                   # Union operation
                   union_set = uid_msg_set.union(range_msg_set)
                   logger.info(f"📋 Union of sets: {union_set}")
                   
                   # Intersection operation
                   intersection_set = uid_msg_set.intersection(range_msg_set)
                   logger.info(f"📋 Intersection of sets: {intersection_set}")
                   
                   # Difference operation
                   difference_set = range_msg_set.subtract(uid_msg_set)
                   logger.info(f"📋 Difference of sets: {difference_set}")
               
               # Demonstrate batch processing
               if hasattr(self, 'recent_messages') and not self.recent_messages.is_empty():
                   logger.info(f"📋 Batch processing demonstration:")
                   
                   batch_count = 0
                   for batch in self.recent_messages.iter_batches(batch_size=10):
                       batch_count += 1
                       logger.info(f"  • Batch {batch_count}: {len(batch)} messages")
                       
                       if batch_count >= 3:  # Limit demonstration
                           break
                   
           except Exception as e:
               logger.error(f"Failed to demonstrate MessageSet usage: {e}")


   def main():
       """
       Main function to run the basic IMAP example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"  # or your IMAP server
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"  # Use app password for Gmail
       PORT = 993
       
       # Create and run the example
       example = BasicIMAPExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_basic_operations()
           logger.info("🎉 Basic IMAP example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Key Concepts Demonstrated
-------------------------

1. **UID-Based Operations**
   - All operations use UIDs for reliability
   - UID services ensure consistent behavior
   - No sequence number dependencies

2. **MessageSet Integration**
   - Created from UIDs, ranges, and search results
   - Automatic optimization for efficiency
   - Set operations (union, intersection, difference)
   - Batch processing capabilities

3. **Proper Error Handling**
   - Specific exception types for different failures
   - Graceful degradation on errors
   - Comprehensive logging

4. **Resource Management**
   - Context managers for automatic cleanup
   - Connection pooling support
   - Timeout configuration

5. **Production Patterns**
   - Secure SSL connections
   - Proper authentication
   - Status monitoring
   - Performance considerations

Best Practices Shown
--------------------

✅ **DO:**

- Use UID-based services for all operations

- Create MessageSet objects from UIDs

- Implement proper error handling

- Use context managers

- Log operations for debugging

❌ **DON'T:**

- Use sequence numbers in production

- Ignore connection errors

- Forget to close connections

- Skip error handling

- Use hardcoded credentials

Next Steps
----------

This example provides the foundation for IMAP operations. For more advanced patterns, see:

- :doc:`uid_search_operations` - Advanced search patterns

- :doc:`mailbox_management` - Mailbox operations

- :doc:`message_set_usage` - Advanced MessageSet usage

- :doc:`production_patterns` - Production-ready patterns
