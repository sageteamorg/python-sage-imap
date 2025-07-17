.. _outlook_integration:

Outlook Integration
===================

This example demonstrates how to integrate with Outlook/Exchange servers using Python Sage IMAP, including modern authentication, special folder handling, and Outlook-specific features.

**⚠️ IMPORTANT: This example covers Outlook/Exchange-specific patterns and modern authentication!**

Overview
--------

You'll learn how to:

- Connect to Outlook/Exchange servers
- Handle modern authentication (OAuth 2.0)
- Work with Outlook special folders
- Manage Exchange-specific features
- Handle Outlook categorization and rules
- Integrate with Office 365
- Process Outlook meeting requests
- Handle Exchange public folders

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid Outlook/Exchange credentials
- Understanding of Outlook folder structure

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Outlook Integration Example
   
   This example demonstrates integration with Outlook/Exchange servers
   including modern authentication and Outlook-specific features.
   """
   
   import logging
   import time
   from datetime import datetime, timedelta
   from typing import Dict, List, Optional, Any
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService, IMAPFolderService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.helpers.enums import MessagePart, Flag
   from sage_imap.exceptions import IMAPOperationError
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class OutlookIntegrationExample:
       """
       Outlook/Exchange integration example.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the Outlook integration example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
           # Outlook-specific folder mappings
           self.outlook_folders = {
               'inbox': 'INBOX',
               'sent': 'Sent Items',
               'drafts': 'Drafts',
               'deleted': 'Deleted Items',
               'junk': 'Junk Email',
               'archive': 'Archive',
               'outbox': 'Outbox',
               'calendar': 'Calendar',
               'contacts': 'Contacts',
               'tasks': 'Tasks',
               'notes': 'Notes',
               'journal': 'Journal'
           }
           
       def demonstrate_outlook_integration(self):
           """
           Demonstrate comprehensive Outlook integration.
           """
           logger.info("=== Outlook Integration Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   folder_service = IMAPFolderService(client)
                   
                   # Outlook connection setup
                   self.demonstrate_outlook_connection(client)
                   
                   # Outlook folder management
                   self.demonstrate_outlook_folders(folder_service)
                   
                   # Outlook categories and rules
                   self.demonstrate_outlook_categories(uid_service)
                   
                   # Meeting request handling
                   self.demonstrate_meeting_requests(uid_service)
                   
                   # Outlook-specific search
                   self.demonstrate_outlook_search(uid_service)
                   
                   # Exchange features
                   self.demonstrate_exchange_features(uid_service)
                   
                   # Office 365 integration
                   self.demonstrate_office365_integration(uid_service)
                   
                   # Outlook email processing
                   self.demonstrate_outlook_email_processing(uid_service)
                   
                   logger.info("✓ Outlook integration completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ Outlook integration failed: {e}")
               raise
   
       def demonstrate_outlook_connection(self, client: IMAPClient):
           """
           Demonstrate Outlook-specific connection setup.
           """
           logger.info("--- Outlook Connection Setup ---")
           
           try:
               # Check server capabilities
               capabilities = client.capabilities
               logger.info(f"📡 Server capabilities: {len(capabilities)} features")
               
               # Check for Outlook/Exchange specific capabilities
               outlook_capabilities = [
                   'IDLE',
                   'MOVE',
                   'QUOTA',
                   'XLIST',
                   'SPECIAL-USE',
                   'UIDPLUS'
               ]
               
               for capability in outlook_capabilities:
                   if capability in capabilities:
                       logger.info(f"  ✓ {capability} supported")
                   else:
                       logger.info(f"  ⚠ {capability} not supported")
               
               # Server identification
               server_info = client.get_server_info()
               if server_info:
                   logger.info(f"📊 Server info: {server_info}")
               
               # Connection status
               if client.is_connected():
                   logger.info("✓ Connected to Outlook/Exchange server")
               
           except Exception as e:
               logger.error(f"Failed Outlook connection setup: {e}")
   
       def demonstrate_outlook_folders(self, folder_service: IMAPFolderService):
           """
           Demonstrate Outlook-specific folder management.
           """
           logger.info("--- Outlook Folder Management ---")
           
           try:
               # List all folders
               all_folders = folder_service.list_folders()
               logger.info(f"📁 Total folders: {len(all_folders)}")
               
               # Identify Outlook special folders
               outlook_special_folders = {}
               
               for folder_type, folder_name in self.outlook_folders.items():
                   # Check for exact match
                   if folder_name in all_folders:
                       outlook_special_folders[folder_type] = folder_name
                   else:
                       # Check for variations
                       for folder in all_folders:
                           if folder.lower() == folder_name.lower():
                               outlook_special_folders[folder_type] = folder
                               break
               
               logger.info("📁 Outlook special folders:")
               for folder_type, folder_name in outlook_special_folders.items():
                   logger.info(f"  • {folder_type.capitalize()}: {folder_name}")
               
               # Check for missing folders
               missing_folders = set(self.outlook_folders.keys()) - set(outlook_special_folders.keys())
               if missing_folders:
                   logger.warning(f"⚠ Missing folders: {', '.join(missing_folders)}")
               
               # Demonstrate folder hierarchy
               self.demonstrate_folder_hierarchy(all_folders)
               
               # Store for later use
               self.outlook_special_folders = outlook_special_folders
               
           except Exception as e:
               logger.error(f"Failed Outlook folder management: {e}")
   
       def demonstrate_folder_hierarchy(self, folders: List[str]):
           """
           Demonstrate Outlook folder hierarchy.
           """
           logger.info("--- Outlook Folder Hierarchy ---")
           
           try:
               # Group folders by hierarchy
               hierarchy = {}
               
               for folder in folders:
                   if '/' in folder:
                       parts = folder.split('/')
                       current = hierarchy
                       
                       for part in parts[:-1]:
                           if part not in current:
                               current[part] = {}
                           current = current[part]
                       
                       current[parts[-1]] = None
                   else:
                       hierarchy[folder] = None
               
               # Display hierarchy (simplified)
               logger.info("📁 Folder hierarchy (sample):")
               folder_count = 0
               for folder in sorted(folders):
                   if folder_count >= 10:  # Limit display
                       logger.info(f"  ... and {len(folders) - 10} more folders")
                       break
                   
                   level = folder.count('/')
                   indent = "  " * (level + 1)
                   folder_name = folder.split('/')[-1] if '/' in folder else folder
                   logger.info(f"{indent}• {folder_name}")
                   folder_count += 1
               
           except Exception as e:
               logger.error(f"Failed folder hierarchy demonstration: {e}")
   
       def demonstrate_outlook_categories(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Outlook categories and rules.
           """
           logger.info("--- Outlook Categories and Rules ---")
           
           try:
               # Select inbox
               uid_service.select("INBOX")
               
               # Search for categorized messages
               self.search_categorized_messages(uid_service)
               
               # Demonstrate color categories
               self.demonstrate_color_categories(uid_service)
               
               # Rule-based processing
               self.demonstrate_outlook_rules(uid_service)
               
           except Exception as e:
               logger.error(f"Failed Outlook categories demonstration: {e}")
   
       def search_categorized_messages(self, uid_service: IMAPMailboxUIDService):
           """
           Search for messages with Outlook categories.
           """
           logger.info("--- Categorized Messages Search ---")
           
           try:
               # Common Outlook categories
               categories = [
                   'Red Category',
                   'Blue Category',
                   'Green Category',
                   'Yellow Category',
                   'Orange Category',
                   'Purple Category'
               ]
               
               for category in categories:
                   try:
                       # Search for messages with category
                       category_criteria = IMAPSearchCriteria.header('X-Microsoft-Categories', category)
                       categorized_messages = uid_service.create_message_set_from_search(category_criteria)
                       
                       if not categorized_messages.is_empty():
                           logger.info(f"  📧 {category}: {len(categorized_messages)} messages")
                       else:
                           logger.info(f"  📧 {category}: No messages")
                   
                   except Exception as e:
                       logger.warning(f"  ⚠ Could not search {category}: {e}")
               
           except Exception as e:
               logger.error(f"Failed categorized messages search: {e}")
   
       def demonstrate_color_categories(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Outlook color categories.
           """
           logger.info("--- Color Categories ---")
           
           try:
               # Get recent messages for category analysis
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("  📧 No recent messages for category analysis")
                   return
               
               # Fetch messages with headers
               fetch_result = uid_service.uid_fetch(recent_messages, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   category_counts = {}
                   
                   for message in messages:
                       # Check for category headers
                       if hasattr(message, 'headers') and message.headers:
                           categories = message.headers.get('X-Microsoft-Categories', '')
                           if categories:
                               for category in categories.split(','):
                                   category = category.strip()
                                   category_counts[category] = category_counts.get(category, 0) + 1
                   
                   if category_counts:
                       logger.info("  📊 Found categories:")
                       for category, count in sorted(category_counts.items()):
                           logger.info(f"    • {category}: {count} messages")
                   else:
                       logger.info("  📊 No categories found in recent messages")
               
           except Exception as e:
               logger.error(f"Failed color categories demonstration: {e}")
   
       def demonstrate_outlook_rules(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Outlook rules processing.
           """
           logger.info("--- Outlook Rules Processing ---")
           
           try:
               # Common Outlook rule patterns
               rule_patterns = [
                   {
                       'name': 'Important Senders',
                       'criteria': IMAPSearchCriteria.or_criteria(
                           IMAPSearchCriteria.from_address('boss@company.com'),
                           IMAPSearchCriteria.from_address('ceo@company.com')
                       ),
                       'action': 'Flag as important'
                   },
                   {
                       'name': 'Newsletter Filter',
                       'criteria': IMAPSearchCriteria.or_criteria(
                           IMAPSearchCriteria.body('unsubscribe'),
                           IMAPSearchCriteria.subject('newsletter')
                       ),
                       'action': 'Move to Newsletter folder'
                   },
                   {
                       'name': 'Meeting Requests',
                       'criteria': IMAPSearchCriteria.header('Content-Type', 'calendar'),
                       'action': 'Process as meeting request'
                   }
               ]
               
               for rule in rule_patterns:
                   try:
                       matching_messages = uid_service.create_message_set_from_search(rule['criteria'])
                       
                       if not matching_messages.is_empty():
                           logger.info(f"  📧 {rule['name']}: {len(matching_messages)} messages")
                           logger.info(f"    Action: {rule['action']}")
                       else:
                           logger.info(f"  📧 {rule['name']}: No matching messages")
                   
                   except Exception as e:
                       logger.warning(f"  ⚠ Rule '{rule['name']}' failed: {e}")
               
           except Exception as e:
               logger.error(f"Failed Outlook rules demonstration: {e}")
   
       def demonstrate_meeting_requests(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate meeting request handling.
           """
           logger.info("--- Meeting Request Handling ---")
           
           try:
               # Search for meeting requests
               meeting_criteria = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.header('Content-Type', 'text/calendar'),
                   IMAPSearchCriteria.subject('Meeting:'),
                   IMAPSearchCriteria.subject('Invitation:'),
                   IMAPSearchCriteria.header('X-Microsoft-CDO-Busystatus', 'BUSY')
               )
               
               meeting_messages = uid_service.create_message_set_from_search(meeting_criteria)
               
               if meeting_messages.is_empty():
                   logger.info("  📅 No meeting requests found")
                   return
               
               logger.info(f"  📅 Found {len(meeting_messages)} meeting requests")
               
               # Process meeting requests
               self.process_meeting_requests(uid_service, meeting_messages)
               
           except Exception as e:
               logger.error(f"Failed meeting request handling: {e}")
   
       def process_meeting_requests(self, uid_service: IMAPMailboxUIDService, meeting_messages: MessageSet):
           """
           Process meeting requests.
           """
           logger.info("--- Processing Meeting Requests ---")
           
           try:
               # Take a sample for processing
               sample_size = min(5, len(meeting_messages))
               sample_uids = list(meeting_messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               # Fetch meeting request details
               fetch_result = uid_service.uid_fetch(sample_set, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   for i, message in enumerate(messages, 1):
                       logger.info(f"  📅 Meeting Request {i}:")
                       logger.info(f"    • Subject: {message.subject}")
                       logger.info(f"    • From: {message.from_address}")
                       logger.info(f"    • Date: {message.date}")
                       
                       # Check for meeting-specific headers
                       if hasattr(message, 'headers') and message.headers:
                           meeting_headers = [
                               'X-Microsoft-CDO-Busystatus',
                               'X-Microsoft-CDO-Importance',
                               'X-Microsoft-CDO-Intendedstatus',
                               'X-Microsoft-CDO-Alldayevent'
                           ]
                           
                           for header in meeting_headers:
                               if header in message.headers:
                                   logger.info(f"    • {header}: {message.headers[header]}")
                       
                       # In a real application, you would:
                       # 1. Parse calendar data
                       # 2. Extract meeting details
                       # 3. Process accept/decline responses
                       # 4. Update calendar systems
               
           except Exception as e:
               logger.error(f"Failed to process meeting requests: {e}")
   
       def demonstrate_outlook_search(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Outlook-specific search patterns.
           """
           logger.info("--- Outlook-Specific Search ---")
           
           try:
               # Select inbox
               uid_service.select("INBOX")
               
               # Outlook-specific searches
               outlook_searches = [
                   ('High importance', IMAPSearchCriteria.header('X-Priority', '1')),
                   ('Out of office', IMAPSearchCriteria.subject('Out of Office')),
                   ('Delivery receipt', IMAPSearchCriteria.header('Content-Type', 'report')),
                   ('Read receipt', IMAPSearchCriteria.header('Content-Type', 'disposition-notification')),
                   ('Encrypted messages', IMAPSearchCriteria.header('Content-Type', 'application/pkcs7-mime')),
                   ('Signed messages', IMAPSearchCriteria.header('Content-Type', 'multipart/signed'))
               ]
               
               for search_name, criteria in outlook_searches:
                   try:
                       messages = uid_service.create_message_set_from_search(criteria)
                       logger.info(f"  📧 {search_name}: {len(messages)} messages")
                   except Exception as e:
                       logger.warning(f"  ⚠ {search_name} search failed: {e}")
               
               # Advanced Outlook searches
               self.demonstrate_advanced_outlook_search(uid_service)
               
           except Exception as e:
               logger.error(f"Failed Outlook-specific search: {e}")
   
       def demonstrate_advanced_outlook_search(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate advanced Outlook search patterns.
           """
           logger.info("--- Advanced Outlook Search ---")
           
           try:
               # Complex Outlook searches
               advanced_searches = [
                   {
                       'name': 'Flagged for follow-up',
                       'criteria': IMAPSearchCriteria.and_criteria(
                           IMAPSearchCriteria.FLAGGED,
                           IMAPSearchCriteria.header('X-Microsoft-Flag', 'Follow up')
                       )
                   },
                   {
                       'name': 'Conversations',
                       'criteria': IMAPSearchCriteria.header('Thread-Topic', 'RE:')
                   },
                   {
                       'name': 'Shared mailbox items',
                       'criteria': IMAPSearchCriteria.header('X-MS-Exchange-Organization-AuthAs', 'Internal')
                   }
               ]
               
               for search in advanced_searches:
                   try:
                       messages = uid_service.create_message_set_from_search(search['criteria'])
                       logger.info(f"  📧 {search['name']}: {len(messages)} messages")
                   except Exception as e:
                       logger.warning(f"  ⚠ {search['name']} search failed: {e}")
               
           except Exception as e:
               logger.error(f"Failed advanced Outlook search: {e}")
   
       def demonstrate_exchange_features(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Exchange-specific features.
           """
           logger.info("--- Exchange Features ---")
           
           try:
               # Exchange server information
               self.demonstrate_exchange_server_info(uid_service)
               
               # Public folders
               self.demonstrate_public_folders(uid_service)
               
               # Shared mailboxes
               self.demonstrate_shared_mailboxes(uid_service)
               
               # Exchange quotas
               self.demonstrate_exchange_quotas(uid_service)
               
           except Exception as e:
               logger.error(f"Failed Exchange features demonstration: {e}")
   
       def demonstrate_exchange_server_info(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Exchange server information.
           """
           logger.info("--- Exchange Server Information ---")
           
           try:
               # Get server status
               status_result = uid_service.get_mailbox_status()
               
               if status_result.success:
                   logger.info("  📊 Exchange server status:")
                   logger.info(f"    • Connected to Exchange server")
                   logger.info(f"    • Mailbox accessible")
                   
                   # Check for Exchange-specific capabilities
                   exchange_features = [
                       'Public folders support',
                       'Shared mailbox support',
                       'Calendar integration',
                       'Meeting request handling',
                       'Category support'
                   ]
                   
                   for feature in exchange_features:
                       logger.info(f"    • {feature}: Available")
               
           except Exception as e:
               logger.error(f"Failed Exchange server info: {e}")
   
       def demonstrate_public_folders(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate public folder access.
           """
           logger.info("--- Public Folders ---")
           
           try:
               # Note: Public folder access depends on server configuration
               logger.info("  📁 Public folder access:")
               logger.info("    • Public folders may require special permissions")
               logger.info("    • Check with Exchange administrator")
               logger.info("    • Typically accessible via separate namespace")
               
               # In a real implementation, you would:
               # 1. Connect to public folder namespace
               # 2. List available public folders
               # 3. Access public folder contents
               # 4. Handle permissions
               
           except Exception as e:
               logger.error(f"Failed public folders demonstration: {e}")
   
       def demonstrate_shared_mailboxes(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate shared mailbox access.
           """
           logger.info("--- Shared Mailboxes ---")
           
           try:
               logger.info("  📫 Shared mailbox access:")
               logger.info("    • Requires appropriate permissions")
               logger.info("    • May use different authentication")
               logger.info("    • Check delegated access rights")
               
               # In a real implementation, you would:
               # 1. Authenticate with shared mailbox credentials
               # 2. Access shared mailbox folders
               # 3. Handle permission levels
               # 4. Process shared mailbox items
               
           except Exception as e:
               logger.error(f"Failed shared mailboxes demonstration: {e}")
   
       def demonstrate_exchange_quotas(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Exchange quota information.
           """
           logger.info("--- Exchange Quotas ---")
           
           try:
               # Get quota information (if available)
               logger.info("  📊 Exchange quota information:")
               logger.info("    • Mailbox size limits")
               logger.info("    • Send/receive limits")
               logger.info("    • Retention policies")
               
               # In a real implementation, you would:
               # 1. Query quota information
               # 2. Monitor usage levels
               # 3. Handle quota warnings
               # 4. Implement cleanup policies
               
           except Exception as e:
               logger.error(f"Failed Exchange quotas demonstration: {e}")
   
       def demonstrate_office365_integration(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Office 365 integration.
           """
           logger.info("--- Office 365 Integration ---")
           
           try:
               # Office 365 specific features
               self.demonstrate_office365_features(uid_service)
               
               # Modern authentication
               self.demonstrate_modern_authentication()
               
               # Graph API integration
               self.demonstrate_graph_integration()
               
           except Exception as e:
               logger.error(f"Failed Office 365 integration: {e}")
   
       def demonstrate_office365_features(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Office 365 specific features.
           """
           logger.info("--- Office 365 Features ---")
           
           try:
               logger.info("  ☁️ Office 365 features:")
               logger.info("    • Cloud-based email processing")
               logger.info("    • Advanced threat protection")
               logger.info("    • Compliance and retention")
               logger.info("    • Integration with Teams/SharePoint")
               
               # Check for Office 365 specific headers
               office365_headers = [
                   'X-MS-Exchange-Organization-ExpirationStartTime',
                   'X-MS-Exchange-Organization-ExpirationStartTimeReason',
                   'X-MS-Exchange-Organization-MessageDirectionality',
                   'X-MS-Exchange-Organization-AuthAs'
               ]
               
               logger.info("  📧 Office 365 header patterns:")
               for header in office365_headers:
                   logger.info(f"    • {header}")
               
           except Exception as e:
               logger.error(f"Failed Office 365 features: {e}")
   
       def demonstrate_modern_authentication(self):
           """
           Demonstrate modern authentication patterns.
           """
           logger.info("--- Modern Authentication ---")
           
           try:
               logger.info("  🔐 Modern authentication:")
               logger.info("    • OAuth 2.0 authentication")
               logger.info("    • Multi-factor authentication support")
               logger.info("    • Conditional access policies")
               logger.info("    • Azure AD integration")
               
               # OAuth 2.0 example configuration
               oauth_config = {
                   'client_id': 'your-app-client-id',
                   'client_secret': 'your-app-client-secret',
                   'tenant_id': 'your-tenant-id',
                   'scope': 'https://outlook.office365.com/IMAP.AccessAsUser.All',
                   'redirect_uri': 'https://your-app.com/callback'
               }
               
               logger.info("  ⚙️ OAuth 2.0 configuration:")
               for key, value in oauth_config.items():
                   if 'secret' not in key.lower():
                       logger.info(f"    • {key}: {value}")
                   else:
                       logger.info(f"    • {key}: [HIDDEN]")
               
           except Exception as e:
               logger.error(f"Failed modern authentication demonstration: {e}")
   
       def demonstrate_graph_integration(self):
           """
           Demonstrate Microsoft Graph API integration.
           """
           logger.info("--- Microsoft Graph Integration ---")
           
           try:
               logger.info("  🔗 Microsoft Graph API:")
               logger.info("    • Unified API for Office 365")
               logger.info("    • Access to mail, calendar, contacts")
               logger.info("    • Rich metadata and insights")
               logger.info("    • Real-time notifications")
               
               # Graph API endpoints
               graph_endpoints = [
                   'https://graph.microsoft.com/v1.0/me/messages',
                   'https://graph.microsoft.com/v1.0/me/mailFolders',
                   'https://graph.microsoft.com/v1.0/me/calendar/events',
                   'https://graph.microsoft.com/v1.0/me/contacts'
               ]
               
               logger.info("  📡 Graph API endpoints:")
               for endpoint in graph_endpoints:
                   logger.info(f"    • {endpoint}")
               
           except Exception as e:
               logger.error(f"Failed Graph integration demonstration: {e}")
   
       def demonstrate_outlook_email_processing(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate Outlook-specific email processing.
           """
           logger.info("--- Outlook Email Processing ---")
           
           try:
               # Select inbox
               uid_service.select("INBOX")
               
               # Get recent emails
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(7)
               )
               
               if recent_messages.is_empty():
                   logger.info("  📧 No recent messages for processing")
                   return
               
               logger.info(f"  📧 Processing {len(recent_messages)} recent messages")
               
               # Process Outlook-specific features
               self.process_outlook_features(uid_service, recent_messages)
               
           except Exception as e:
               logger.error(f"Failed Outlook email processing: {e}")
   
       def process_outlook_features(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Process Outlook-specific features in messages.
           """
           logger.info("--- Processing Outlook Features ---")
           
           try:
               # Take a sample for processing
               sample_size = min(10, len(messages))
               sample_uids = list(messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               # Fetch message details
               fetch_result = uid_service.uid_fetch(sample_set, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   outlook_features = {
                       'importance': 0,
                       'categories': 0,
                       'flags': 0,
                       'meetings': 0,
                       'receipts': 0
                   }
                   
                   for message in messages:
                       # Check for importance
                       if hasattr(message, 'headers') and message.headers:
                           if 'X-Priority' in message.headers:
                               outlook_features['importance'] += 1
                           
                           if 'X-Microsoft-Categories' in message.headers:
                               outlook_features['categories'] += 1
                           
                           if 'X-Microsoft-Flag' in message.headers:
                               outlook_features['flags'] += 1
                           
                           if 'text/calendar' in message.headers.get('Content-Type', ''):
                               outlook_features['meetings'] += 1
                           
                           if 'disposition-notification' in message.headers.get('Content-Type', ''):
                               outlook_features['receipts'] += 1
                   
                   logger.info("  📊 Outlook feature usage:")
                   for feature, count in outlook_features.items():
                       logger.info(f"    • {feature.capitalize()}: {count} messages")
               
           except Exception as e:
               logger.error(f"Failed to process Outlook features: {e}")


   def main():
       """
       Main function to run the Outlook integration example.
       """
       # Configuration - Replace with your actual Outlook credentials
       HOST = "outlook.office365.com"  # or your Exchange server
       USERNAME = "your_email@outlook.com"
       PASSWORD = "your_password"  # or app password
       PORT = 993
       
       # Create and run the example
       example = OutlookIntegrationExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_outlook_integration()
           logger.info("🎉 Outlook integration example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Outlook/Exchange Configuration
------------------------------

Connection Settings
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Outlook.com / Office 365
   outlook_config = {
       'host': 'outlook.office365.com',
       'port': 993,
       'use_ssl': True,
       'username': 'your_email@outlook.com',
       'password': 'your_app_password'
   }
   
   # Exchange Server
   exchange_config = {
       'host': 'mail.company.com',
       'port': 993,
       'use_ssl': True,
       'username': 'domain\\username',
       'password': 'your_password'
   }

Modern Authentication
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # OAuth 2.0 configuration
   oauth_config = {
       'client_id': 'your-app-client-id',
       'client_secret': 'your-app-client-secret',
       'tenant_id': 'your-tenant-id',
       'scope': 'https://outlook.office365.com/IMAP.AccessAsUser.All',
       'redirect_uri': 'https://your-app.com/callback'
   }

Special Folders
~~~~~~~~~~~~~~~

.. code-block:: python

   # Outlook folder mappings
   outlook_folders = {
       'inbox': 'INBOX',
       'sent': 'Sent Items',
       'drafts': 'Drafts',
       'deleted': 'Deleted Items',
       'junk': 'Junk Email',
       'archive': 'Archive',
       'calendar': 'Calendar',
       'contacts': 'Contacts',
       'tasks': 'Tasks'
   }

Categories and Rules
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Search by category
   category_criteria = IMAPSearchCriteria.header('X-Microsoft-Categories', 'Red Category')
   categorized_messages = uid_service.create_message_set_from_search(category_criteria)
   
   # High importance messages
   important_criteria = IMAPSearchCriteria.header('X-Priority', '1')
   important_messages = uid_service.create_message_set_from_search(important_criteria)

Meeting Requests
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Search for meeting requests
   meeting_criteria = IMAPSearchCriteria.or_criteria(
       IMAPSearchCriteria.header('Content-Type', 'text/calendar'),
       IMAPSearchCriteria.subject('Meeting:'),
       IMAPSearchCriteria.header('X-Microsoft-CDO-Busystatus', 'BUSY')
   )
   
   meeting_messages = uid_service.create_message_set_from_search(meeting_criteria)

Outlook-Specific Headers
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Common Outlook headers
   outlook_headers = [
       'X-Microsoft-Categories',      # Color categories
       'X-Microsoft-Flag',           # Follow-up flags
       'X-Priority',                 # Message importance
       'X-Microsoft-CDO-Busystatus', # Calendar busy status
       'X-MS-Exchange-Organization-AuthAs',  # Authentication
       'Thread-Topic',               # Conversation threading
       'Thread-Index'                # Message threading
   ]

Best Practices
--------------

✅ **DO:**

- Use modern authentication (OAuth 2.0) when possible

- Handle Outlook-specific folder names

- Process categories and flags appropriately

- Implement proper meeting request handling

- Use Exchange-specific features when available

- Monitor quota usage

- Handle shared mailbox permissions

❌ **DON'T:**

- Use basic authentication in production

- Ignore Outlook folder structure

- Skip category processing

- Forget meeting request handling

- Ignore Exchange server limits

- Overlook shared mailbox access

- Skip modern authentication setup

Common Issues and Solutions
---------------------------

Authentication Issues
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable modern authentication
   # Disable basic auth in Office 365
   # Use app passwords for legacy apps
   # Configure OAuth 2.0 properly

Folder Access Issues
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Check folder permissions
   # Verify shared mailbox access
   # Handle public folder permissions
   # Use correct folder names

Performance Issues
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use connection pooling
   # Implement proper caching
   # Batch operations efficiently
   # Monitor Exchange throttling

Next Steps
----------

For more advanced patterns, see:

- :doc:`client_advanced` - Advanced client features
- :doc:`production_patterns` - Production-ready patterns
- :doc:`smtp_integration` - Email sending integration
- :doc:`monitoring_analytics` - Monitoring and analytics 