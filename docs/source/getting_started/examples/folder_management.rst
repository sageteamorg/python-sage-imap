.. _folder_management:

Folder Management
=================

This example demonstrates comprehensive folder management operations using Python Sage IMAP with proper error handling and best practices.

**⚠️ IMPORTANT: This example demonstrates safe folder operations with proper validation!**

Overview
--------

You'll learn how to:

- List and explore folder hierarchies
- Create and delete folders safely
- Rename and move folders
- Manage folder subscriptions
- Handle folder permissions
- Implement folder organization patterns
- Work with special folders (INBOX, Sent, Drafts, etc.)

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of IMAP folder concepts

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Folder Management Example
   
   This example demonstrates comprehensive folder management operations
   with proper error handling and best practices.
   """
   
   import logging
   import time
   from datetime import datetime
   from typing import List, Dict, Optional, Set
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPFolderService, IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.exceptions import IMAPOperationError, IMAPFolderError
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class FolderManagementExample:
       """
       Comprehensive folder management operations example.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the folder management example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
       def demonstrate_folder_operations(self):
           """
           Demonstrate comprehensive folder management operations.
           """
           logger.info("=== Folder Management Operations Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   folder_service = IMAPFolderService(client)
                   uid_service = IMAPMailboxUIDService(client)
                   
                   # Explore folder hierarchy
                   self.explore_folder_hierarchy(folder_service)
                   
                   # Create and manage folders
                   self.demonstrate_folder_creation(folder_service)
                   
                   # Folder organization patterns
                   self.demonstrate_folder_organization(folder_service)
                   
                   # Folder subscriptions
                   self.demonstrate_folder_subscriptions(folder_service)
                   
                   # Move messages between folders
                   self.demonstrate_message_folder_operations(folder_service, uid_service)
                   
                   # Folder maintenance
                   self.demonstrate_folder_maintenance(folder_service, uid_service)
                   
                   # Special folder handling
                   self.demonstrate_special_folders(folder_service)
                   
                   # Cleanup demo folders
                   self.cleanup_demo_folders(folder_service)
                   
                   logger.info("✓ Folder management operations completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ Folder management operations failed: {e}")
               raise
   
       def explore_folder_hierarchy(self, folder_service: IMAPFolderService):
           """
           Explore and analyze the folder hierarchy.
           """
           logger.info("--- Exploring Folder Hierarchy ---")
           
           try:
               # List all folders
               all_folders = folder_service.list_folders()
               logger.info(f"📁 Total folders: {len(all_folders)}")
               
               # Analyze folder structure
               self.analyze_folder_structure(all_folders)
               
               # Find special folders
               self.identify_special_folders(all_folders)
               
               # Show folder tree
               self.display_folder_tree(all_folders)
               
               # Store for later use
               self.all_folders = all_folders
               
           except Exception as e:
               logger.error(f"Failed to explore folder hierarchy: {e}")
   
       def analyze_folder_structure(self, folders: List[str]):
           """
           Analyze the folder structure and hierarchy.
           """
           logger.info("--- Analyzing Folder Structure ---")
           
           try:
               # Categorize folders by type
               system_folders = []
               user_folders = []
               nested_folders = []
               
               for folder in folders:
                   if folder.upper() in ['INBOX', 'SENT', 'DRAFTS', 'TRASH', 'SPAM', 'JUNK']:
                       system_folders.append(folder)
                   elif '/' in folder or '.' in folder:
                       nested_folders.append(folder)
                   else:
                       user_folders.append(folder)
               
               logger.info(f"📊 Folder Analysis:")
               logger.info(f"  • System folders: {len(system_folders)}")
               logger.info(f"  • User folders: {len(user_folders)}")
               logger.info(f"  • Nested folders: {len(nested_folders)}")
               
               # Show hierarchy depth
               max_depth = 0
               for folder in folders:
                   depth = len(folder.split('/')) - 1
                   max_depth = max(max_depth, depth)
               
               logger.info(f"  • Maximum depth: {max_depth}")
               
               # Show folder naming patterns
               self.analyze_naming_patterns(folders)
               
           except Exception as e:
               logger.error(f"Failed to analyze folder structure: {e}")
   
       def analyze_naming_patterns(self, folders: List[str]):
           """
           Analyze folder naming patterns.
           """
           logger.info("--- Folder Naming Patterns ---")
           
           try:
               # Common patterns
               patterns = {
                   'date_based': [],
                   'project_based': [],
                   'person_based': [],
                   'category_based': []
               }
               
               for folder in folders:
                   folder_lower = folder.lower()
                   
                   # Date-based (containing year)
                   if any(year in folder for year in ['2024', '2023', '2022', '2021']):
                       patterns['date_based'].append(folder)
                   
                   # Project-based (containing "project")
                   elif 'project' in folder_lower:
                       patterns['project_based'].append(folder)
                   
                   # Person-based (containing common names or "from")
                   elif any(word in folder_lower for word in ['from', 'john', 'jane', 'team']):
                       patterns['person_based'].append(folder)
                   
                   # Category-based (containing category words)
                   elif any(word in folder_lower for word in ['work', 'personal', 'finance', 'travel']):
                       patterns['category_based'].append(folder)
               
               logger.info("📊 Naming Pattern Analysis:")
               for pattern_type, pattern_folders in patterns.items():
                   if pattern_folders:
                       logger.info(f"  • {pattern_type.replace('_', ' ').title()}: {len(pattern_folders)}")
                       for folder in pattern_folders[:3]:  # Show first 3
                           logger.info(f"    - {folder}")
                       if len(pattern_folders) > 3:
                           logger.info(f"    ... and {len(pattern_folders) - 3} more")
               
           except Exception as e:
               logger.error(f"Failed to analyze naming patterns: {e}")
   
       def identify_special_folders(self, folders: List[str]):
           """
           Identify and validate special folders.
           """
           logger.info("--- Special Folders Identification ---")
           
           try:
               # Standard special folders
               special_folders = {
                   'INBOX': ['INBOX', 'Inbox'],
                   'SENT': ['Sent', 'Sent Items', 'Sent Messages', 'SENT'],
                   'DRAFTS': ['Drafts', 'Draft', 'DRAFTS'],
                   'TRASH': ['Trash', 'Deleted Items', 'Deleted Messages', 'TRASH'],
                   'SPAM': ['Spam', 'Junk', 'Junk E-mail', 'SPAM'],
                   'ARCHIVE': ['Archive', 'All Mail', 'ARCHIVE']
               }
               
               found_special = {}
               
               for folder_type, possible_names in special_folders.items():
                   for folder in folders:
                       if folder in possible_names:
                           found_special[folder_type] = folder
                           break
               
               logger.info("📁 Special Folders Found:")
               for folder_type, folder_name in found_special.items():
                   logger.info(f"  • {folder_type}: {folder_name}")
               
               # Check for missing special folders
               missing_folders = set(special_folders.keys()) - set(found_special.keys())
               if missing_folders:
                   logger.warning(f"⚠ Missing special folders: {', '.join(missing_folders)}")
               
               # Store for later use
               self.special_folders = found_special
               
           except Exception as e:
               logger.error(f"Failed to identify special folders: {e}")
   
       def display_folder_tree(self, folders: List[str]):
           """
           Display folder hierarchy as a tree.
           """
           logger.info("--- Folder Tree Structure ---")
           
           try:
               # Build tree structure
               tree = {}
               
               for folder in sorted(folders):
                   parts = folder.split('/')
                   current = tree
                   
                   for part in parts:
                       if part not in current:
                           current[part] = {}
                       current = current[part]
               
               # Display tree (first 2 levels only for demo)
               logger.info("📁 Folder Tree (showing first 2 levels):")
               self._display_tree_level(tree, "", 0, max_depth=2)
               
           except Exception as e:
               logger.error(f"Failed to display folder tree: {e}")
   
       def _display_tree_level(self, tree: Dict, prefix: str, level: int, max_depth: int = 3):
           """
           Recursively display tree levels.
           """
           if level >= max_depth:
               return
               
           items = list(tree.items())
           for i, (name, subtree) in enumerate(items):
               is_last = i == len(items) - 1
               current_prefix = "└── " if is_last else "├── "
               logger.info(f"{prefix}{current_prefix}{name}")
               
               if subtree and level < max_depth - 1:
                   next_prefix = prefix + ("    " if is_last else "│   ")
                   self._display_tree_level(subtree, next_prefix, level + 1, max_depth)
   
       def demonstrate_folder_creation(self, folder_service: IMAPFolderService):
           """
           Demonstrate folder creation operations.
           """
           logger.info("--- Folder Creation Operations ---")
           
           try:
               # Create simple folder
               self.create_simple_folder(folder_service)
               
               # Create nested folder structure
               self.create_nested_folders(folder_service)
               
               # Create folders with special characters
               self.create_special_folders(folder_service)
               
               logger.info("  ✓ Folder creation operations completed")
               
           except Exception as e:
               logger.error(f"Failed folder creation operations: {e}")
   
       def create_simple_folder(self, folder_service: IMAPFolderService):
           """
           Create simple folders with validation.
           """
           logger.info("--- Creating Simple Folders ---")
           
           try:
               # Folders to create
               simple_folders = [
                   "Demo_Folder",
                   "Test_Archive",
                   "Temp_Processing"
               ]
               
               for folder_name in simple_folders:
                   try:
                       logger.info(f"  📁 Creating folder: {folder_name}")
                       
                       # Check if folder already exists
                       existing_folders = folder_service.list_folders()
                       if folder_name in existing_folders:
                           logger.info(f"    ⚠ Folder {folder_name} already exists")
                           continue
                       
                       # Create folder
                       result = folder_service.create_folder(folder_name)
                       
                       if result.success:
                           logger.info(f"    ✓ Created folder: {folder_name}")
                       else:
                           logger.error(f"    ❌ Failed to create {folder_name}: {result.error_message}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Error creating {folder_name}: {e}")
               
           except Exception as e:
               logger.error(f"Failed to create simple folders: {e}")
   
       def create_nested_folders(self, folder_service: IMAPFolderService):
           """
           Create nested folder structures.
           """
           logger.info("--- Creating Nested Folders ---")
           
           try:
               # Nested folder structure
               nested_structure = [
                   "Projects",
                   "Projects/Alpha",
                   "Projects/Alpha/Documents",
                   "Projects/Alpha/Meetings",
                   "Projects/Beta",
                   "Projects/Beta/Reports",
                   "Archive",
                   "Archive/2024",
                   "Archive/2024/Q1",
                   "Archive/2024/Q2"
               ]
               
               for folder_path in nested_structure:
                   try:
                       logger.info(f"  📁 Creating nested folder: {folder_path}")
                       
                       # Check if folder exists
                       existing_folders = folder_service.list_folders()
                       if folder_path in existing_folders:
                           logger.info(f"    ⚠ Folder {folder_path} already exists")
                           continue
                       
                       # Create folder (parent folders should be created automatically)
                       result = folder_service.create_folder(folder_path)
                       
                       if result.success:
                           logger.info(f"    ✓ Created nested folder: {folder_path}")
                       else:
                           logger.error(f"    ❌ Failed to create {folder_path}: {result.error_message}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Error creating {folder_path}: {e}")
               
           except Exception as e:
               logger.error(f"Failed to create nested folders: {e}")
   
       def create_special_folders(self, folder_service: IMAPFolderService):
           """
           Create folders with special characters (where supported).
           """
           logger.info("--- Creating Folders with Special Characters ---")
           
           try:
               # Special character folders (may not be supported by all servers)
               special_folders = [
                   "Test & Development",
                   "Reports (Monthly)",
                   "Archive-2024",
                   "Temp_Folder"
               ]
               
               for folder_name in special_folders:
                   try:
                       logger.info(f"  📁 Creating special folder: {folder_name}")
                       
                       # Check if folder exists
                       existing_folders = folder_service.list_folders()
                       if folder_name in existing_folders:
                           logger.info(f"    ⚠ Folder {folder_name} already exists")
                           continue
                       
                       # Create folder
                       result = folder_service.create_folder(folder_name)
                       
                       if result.success:
                           logger.info(f"    ✓ Created special folder: {folder_name}")
                       else:
                           logger.warning(f"    ⚠ Failed to create {folder_name}: {result.error_message}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error creating {folder_name}: {e}")
               
               logger.info("  ✓ Special folder creation completed")
               
           except Exception as e:
               logger.error(f"Failed to create special folders: {e}")
   
       def demonstrate_folder_organization(self, folder_service: IMAPFolderService):
           """
           Demonstrate folder organization patterns.
           """
           logger.info("--- Folder Organization Patterns ---")
           
           try:
               # Date-based organization
               self.create_date_based_organization(folder_service)
               
               # Project-based organization
               self.create_project_based_organization(folder_service)
               
               # Category-based organization
               self.create_category_based_organization(folder_service)
               
               logger.info("  ✓ Folder organization patterns completed")
               
           except Exception as e:
               logger.error(f"Failed folder organization: {e}")
   
       def create_date_based_organization(self, folder_service: IMAPFolderService):
           """
           Create date-based folder organization.
           """
           logger.info("--- Date-Based Organization ---")
           
           try:
               current_year = datetime.now().year
               
               # Create yearly structure
               date_folders = [
                   f"Archive/{current_year}",
                   f"Archive/{current_year}/Q1",
                   f"Archive/{current_year}/Q2",
                   f"Archive/{current_year}/Q3",
                   f"Archive/{current_year}/Q4",
                   f"Archive/{current_year-1}",
                   f"Archive/{current_year-1}/Important"
               ]
               
               for folder in date_folders:
                   try:
                       existing_folders = folder_service.list_folders()
                       if folder not in existing_folders:
                           result = folder_service.create_folder(folder)
                           if result.success:
                               logger.info(f"    ✓ Created date folder: {folder}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error creating date folder {folder}: {e}")
               
           except Exception as e:
               logger.error(f"Failed date-based organization: {e}")
   
       def create_project_based_organization(self, folder_service: IMAPFolderService):
           """
           Create project-based folder organization.
           """
           logger.info("--- Project-Based Organization ---")
           
           try:
               # Create project structure
               project_folders = [
                   "Projects/Website_Redesign",
                   "Projects/Website_Redesign/Design",
                   "Projects/Website_Redesign/Development",
                   "Projects/Website_Redesign/Testing",
                   "Projects/Mobile_App",
                   "Projects/Mobile_App/Requirements",
                   "Projects/Mobile_App/Development",
                   "Projects/Database_Migration",
                   "Projects/Database_Migration/Planning",
                   "Projects/Database_Migration/Execution"
               ]
               
               for folder in project_folders:
                   try:
                       existing_folders = folder_service.list_folders()
                       if folder not in existing_folders:
                           result = folder_service.create_folder(folder)
                           if result.success:
                               logger.info(f"    ✓ Created project folder: {folder}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error creating project folder {folder}: {e}")
               
           except Exception as e:
               logger.error(f"Failed project-based organization: {e}")
   
       def create_category_based_organization(self, folder_service: IMAPFolderService):
           """
           Create category-based folder organization.
           """
           logger.info("--- Category-Based Organization ---")
           
           try:
               # Create category structure
               category_folders = [
                   "Categories/Work",
                   "Categories/Work/Meetings",
                   "Categories/Work/Reports",
                   "Categories/Work/HR",
                   "Categories/Personal",
                   "Categories/Personal/Family",
                   "Categories/Personal/Finance",
                   "Categories/Personal/Travel",
                   "Categories/Technical",
                   "Categories/Technical/Documentation",
                   "Categories/Technical/Issues"
               ]
               
               for folder in category_folders:
                   try:
                       existing_folders = folder_service.list_folders()
                       if folder not in existing_folders:
                           result = folder_service.create_folder(folder)
                           if result.success:
                               logger.info(f"    ✓ Created category folder: {folder}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error creating category folder {folder}: {e}")
               
           except Exception as e:
               logger.error(f"Failed category-based organization: {e}")
   
       def demonstrate_folder_subscriptions(self, folder_service: IMAPFolderService):
           """
           Demonstrate folder subscription operations.
           """
           logger.info("--- Folder Subscription Operations ---")
           
           try:
               # List subscribed folders
               self.list_subscribed_folders(folder_service)
               
               # Subscribe to folders
               self.subscribe_to_folders(folder_service)
               
               # Unsubscribe from folders
               self.unsubscribe_from_folders(folder_service)
               
               logger.info("  ✓ Folder subscription operations completed")
               
           except Exception as e:
               logger.error(f"Failed folder subscription operations: {e}")
   
       def list_subscribed_folders(self, folder_service: IMAPFolderService):
           """
           List currently subscribed folders.
           """
           logger.info("--- Listing Subscribed Folders ---")
           
           try:
               # Get subscribed folders
               subscribed_folders = folder_service.list_subscribed_folders()
               
               if subscribed_folders:
                   logger.info(f"  📁 Subscribed folders ({len(subscribed_folders)}):")
                   for folder in subscribed_folders[:10]:  # Show first 10
                       logger.info(f"    • {folder}")
                   
                   if len(subscribed_folders) > 10:
                       logger.info(f"    ... and {len(subscribed_folders) - 10} more")
               else:
                   logger.info("  📁 No subscribed folders found")
               
           except Exception as e:
               logger.error(f"Failed to list subscribed folders: {e}")
   
       def subscribe_to_folders(self, folder_service: IMAPFolderService):
           """
           Subscribe to specific folders.
           """
           logger.info("--- Subscribing to Folders ---")
           
           try:
               # Folders to subscribe to
               folders_to_subscribe = [
                   "Demo_Folder",
                   "Projects/Alpha",
                   "Archive/2024"
               ]
               
               for folder in folders_to_subscribe:
                   try:
                       logger.info(f"  📁 Subscribing to: {folder}")
                       
                       result = folder_service.subscribe_folder(folder)
                       
                       if result.success:
                           logger.info(f"    ✓ Subscribed to: {folder}")
                       else:
                           logger.warning(f"    ⚠ Failed to subscribe to {folder}: {result.error_message}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error subscribing to {folder}: {e}")
               
           except Exception as e:
               logger.error(f"Failed to subscribe to folders: {e}")
   
       def unsubscribe_from_folders(self, folder_service: IMAPFolderService):
           """
           Unsubscribe from specific folders.
           """
           logger.info("--- Unsubscribing from Folders ---")
           
           try:
               # Folders to unsubscribe from
               folders_to_unsubscribe = [
                   "Temp_Processing",
                   "Test_Archive"
               ]
               
               for folder in folders_to_unsubscribe:
                   try:
                       logger.info(f"  📁 Unsubscribing from: {folder}")
                       
                       result = folder_service.unsubscribe_folder(folder)
                       
                       if result.success:
                           logger.info(f"    ✓ Unsubscribed from: {folder}")
                       else:
                           logger.warning(f"    ⚠ Failed to unsubscribe from {folder}: {result.error_message}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error unsubscribing from {folder}: {e}")
               
           except Exception as e:
               logger.error(f"Failed to unsubscribe from folders: {e}")
   
       def demonstrate_message_folder_operations(self, folder_service: IMAPFolderService, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate moving messages between folders.
           """
           logger.info("--- Message Folder Operations ---")
           
           try:
               # Move messages between folders
               self.move_messages_between_folders(uid_service)
               
               # Copy messages to folders
               self.copy_messages_to_folders(uid_service)
               
               # Organize messages by folder
               self.organize_messages_by_folder(uid_service)
               
               logger.info("  ✓ Message folder operations completed")
               
           except Exception as e:
               logger.error(f"Failed message folder operations: {e}")
   
       def move_messages_between_folders(self, uid_service: IMAPMailboxUIDService):
           """
           Move messages between folders.
           """
           logger.info("--- Moving Messages Between Folders ---")
           
           try:
               # Select INBOX
               uid_service.select("INBOX")
               
               # Find old messages to move
               old_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.before((datetime.now() - timedelta(days=90)).strftime("%d-%b-%Y"))
               )
               
               if old_messages.is_empty():
                   logger.info("  📧 No old messages to move")
                   return
               
               # Take a small sample
               sample_size = min(3, len(old_messages))
               sample_uids = list(old_messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"  📧 Moving {len(sample_set)} old messages to Archive")
               
               # Move to archive folder
               move_result = uid_service.uid_move(sample_set, "Archive")
               
               if move_result.success:
                   logger.info(f"    ✓ Moved {len(sample_set)} messages to Archive")
               else:
                   logger.warning(f"    ⚠ Failed to move messages: {move_result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to move messages: {e}")
   
       def copy_messages_to_folders(self, uid_service: IMAPMailboxUIDService):
           """
           Copy messages to backup folders.
           """
           logger.info("--- Copying Messages to Folders ---")
           
           try:
               # Select INBOX
               uid_service.select("INBOX")
               
               # Find important messages to copy
               important_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.FLAGGED
               )
               
               if important_messages.is_empty():
                   logger.info("  📧 No important messages to copy")
                   return
               
               # Take a small sample
               sample_size = min(2, len(important_messages))
               sample_uids = list(important_messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"  📧 Copying {len(sample_set)} important messages to backup")
               
               # Copy to backup folder
               copy_result = uid_service.uid_copy(sample_set, "Archive/Important")
               
               if copy_result.success:
                   logger.info(f"    ✓ Copied {len(sample_set)} messages to Archive/Important")
               else:
                   logger.warning(f"    ⚠ Failed to copy messages: {copy_result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to copy messages: {e}")
   
       def organize_messages_by_folder(self, uid_service: IMAPMailboxUIDService):
           """
           Organize messages into appropriate folders based on content.
           """
           logger.info("--- Organizing Messages by Folder ---")
           
           try:
               # Select INBOX
               uid_service.select("INBOX")
               
               # Organization rules
               organization_rules = [
                   {
                       'criteria': IMAPSearchCriteria.subject("meeting"),
                       'folder': "Categories/Work/Meetings",
                       'description': "Meeting-related messages"
                   },
                   {
                       'criteria': IMAPSearchCriteria.subject("report"),
                       'folder': "Categories/Work/Reports",
                       'description': "Report messages"
                   },
                   {
                       'criteria': IMAPSearchCriteria.from_address("@finance.com"),
                       'folder': "Categories/Personal/Finance",
                       'description': "Finance messages"
                   }
               ]
               
               for rule in organization_rules:
                   try:
                       # Find messages matching criteria
                       matching_messages = uid_service.create_message_set_from_search(rule['criteria'])
                       
                       if not matching_messages.is_empty():
                           # Take a small sample
                           sample_size = min(2, len(matching_messages))
                           sample_uids = list(matching_messages.parsed_ids)[:sample_size]
                           sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
                           
                           logger.info(f"  📧 {rule['description']}: {len(sample_set)} messages")
                           
                           # Move to appropriate folder
                           move_result = uid_service.uid_move(sample_set, rule['folder'])
                           
                           if move_result.success:
                               logger.info(f"    ✓ Moved to {rule['folder']}")
                           else:
                               logger.warning(f"    ⚠ Failed to move: {move_result.error_message}")
                       else:
                           logger.info(f"  📧 {rule['description']}: No matching messages")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error organizing {rule['description']}: {e}")
               
           except Exception as e:
               logger.error(f"Failed to organize messages: {e}")
   
       def demonstrate_folder_maintenance(self, folder_service: IMAPFolderService, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate folder maintenance operations.
           """
           logger.info("--- Folder Maintenance Operations ---")
           
           try:
               # Clean empty folders
               self.clean_empty_folders(folder_service, uid_service)
               
               # Rename folders
               self.rename_folders(folder_service)
               
               # Folder statistics
               self.generate_folder_statistics(folder_service, uid_service)
               
               logger.info("  ✓ Folder maintenance operations completed")
               
           except Exception as e:
               logger.error(f"Failed folder maintenance operations: {e}")
   
       def clean_empty_folders(self, folder_service: IMAPFolderService, uid_service: IMAPMailboxUIDService):
           """
           Clean up empty folders.
           """
           logger.info("--- Cleaning Empty Folders ---")
           
           try:
               # Get all folders
               all_folders = folder_service.list_folders()
               
               empty_folders = []
               
               # Check each folder for messages
               for folder in all_folders:
                   try:
                       # Skip system folders
                       if folder.upper() in ['INBOX', 'SENT', 'DRAFTS', 'TRASH']:
                           continue
                       
                       # Select folder
                       select_result = uid_service.select(folder)
                       
                       if select_result.success:
                           # Check if folder is empty
                           all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
                           
                           if all_messages.is_empty():
                               empty_folders.append(folder)
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error checking folder {folder}: {e}")
               
               if empty_folders:
                   logger.info(f"  📁 Found {len(empty_folders)} empty folders:")
                   for folder in empty_folders:
                       logger.info(f"    • {folder}")
                   
                   # In practice, you might want to delete these folders
                   # For demo, we'll just report them
                   logger.info("  ℹ In production, consider deleting empty folders")
               else:
                   logger.info("  📁 No empty folders found")
               
           except Exception as e:
               logger.error(f"Failed to clean empty folders: {e}")
   
       def rename_folders(self, folder_service: IMAPFolderService):
           """
           Demonstrate folder renaming operations.
           """
           logger.info("--- Renaming Folders ---")
           
           try:
               # Folders to rename
               rename_operations = [
                   {
                       'old_name': 'Temp_Processing',
                       'new_name': 'Processing_Temp',
                       'reason': 'Better naming convention'
                   },
                   {
                       'old_name': 'Test_Archive',
                       'new_name': 'Archive_Test',
                       'reason': 'Consistent naming'
                   }
               ]
               
               for operation in rename_operations:
                   try:
                       old_name = operation['old_name']
                       new_name = operation['new_name']
                       
                       logger.info(f"  📁 Renaming {old_name} to {new_name}")
                       logger.info(f"    Reason: {operation['reason']}")
                       
                       # Check if old folder exists
                       existing_folders = folder_service.list_folders()
                       if old_name not in existing_folders:
                           logger.info(f"    ⚠ Folder {old_name} does not exist")
                           continue
                       
                       # Check if new name already exists
                       if new_name in existing_folders:
                           logger.info(f"    ⚠ Folder {new_name} already exists")
                           continue
                       
                       # Rename folder
                       rename_result = folder_service.rename_folder(old_name, new_name)
                       
                       if rename_result.success:
                           logger.info(f"    ✓ Renamed {old_name} to {new_name}")
                       else:
                           logger.warning(f"    ⚠ Failed to rename: {rename_result.error_message}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error renaming folder: {e}")
               
           except Exception as e:
               logger.error(f"Failed to rename folders: {e}")
   
       def generate_folder_statistics(self, folder_service: IMAPFolderService, uid_service: IMAPMailboxUIDService):
           """
           Generate statistics about folder usage.
           """
           logger.info("--- Folder Statistics ---")
           
           try:
               # Get all folders
               all_folders = folder_service.list_folders()
               
               folder_stats = []
               
               # Analyze each folder
               for folder in all_folders[:10]:  # Limit to first 10 for demo
                   try:
                       # Select folder
                       select_result = uid_service.select(folder)
                       
                       if select_result.success:
                           # Get folder statistics
                           status_result = uid_service.get_mailbox_status()
                           
                           if status_result.success:
                               status = status_result.metadata
                               
                               folder_stats.append({
                                   'name': folder,
                                   'total_messages': status.get('EXISTS', 0),
                                   'unread_messages': status.get('UNSEEN', 0),
                                   'recent_messages': status.get('RECENT', 0)
                               })
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error getting stats for {folder}: {e}")
               
               # Display statistics
               if folder_stats:
                   logger.info(f"  📊 Folder Statistics (showing first 10):")
                   logger.info(f"    {'Folder':<30} {'Total':<8} {'Unread':<8} {'Recent':<8}")
                   logger.info(f"    {'-' * 30} {'-' * 8} {'-' * 8} {'-' * 8}")
                   
                   for stats in folder_stats:
                       logger.info(f"    {stats['name']:<30} {stats['total_messages']:<8} "
                                  f"{stats['unread_messages']:<8} {stats['recent_messages']:<8}")
                   
                   # Summary
                   total_messages = sum(stats['total_messages'] for stats in folder_stats)
                   total_unread = sum(stats['unread_messages'] for stats in folder_stats)
                   
                   logger.info(f"  📊 Summary:")
                   logger.info(f"    Total messages: {total_messages}")
                   logger.info(f"    Total unread: {total_unread}")
                   logger.info(f"    Read percentage: {((total_messages - total_unread) / total_messages * 100):.1f}%" if total_messages > 0 else "0%")
               
           except Exception as e:
               logger.error(f"Failed to generate folder statistics: {e}")
   
       def demonstrate_special_folders(self, folder_service: IMAPFolderService):
           """
           Demonstrate special folder handling.
           """
           logger.info("--- Special Folder Handling ---")
           
           try:
               # Ensure required special folders exist
               required_folders = {
                   'Archive': 'For archiving old messages',
                   'Processed': 'For processed messages',
                   'Backup': 'For backup purposes'
               }
               
               existing_folders = folder_service.list_folders()
               
               for folder_name, description in required_folders.items():
                   if folder_name not in existing_folders:
                       logger.info(f"  📁 Creating required folder: {folder_name}")
                       logger.info(f"    Purpose: {description}")
                       
                       result = folder_service.create_folder(folder_name)
                       
                       if result.success:
                           logger.info(f"    ✓ Created: {folder_name}")
                       else:
                           logger.warning(f"    ⚠ Failed to create {folder_name}: {result.error_message}")
                   else:
                       logger.info(f"  📁 Required folder exists: {folder_name}")
               
               # Validate special folder structure
               self.validate_special_folder_structure(folder_service)
               
           except Exception as e:
               logger.error(f"Failed special folder handling: {e}")
   
       def validate_special_folder_structure(self, folder_service: IMAPFolderService):
           """
           Validate that special folders have proper structure.
           """
           logger.info("--- Validating Special Folder Structure ---")
           
           try:
               # Expected structure
               expected_structure = {
                   'INBOX': 'Must exist',
                   'Sent': 'Should exist',
                   'Drafts': 'Should exist',
                   'Trash': 'Should exist',
                   'Archive': 'Recommended',
                   'Archive/Important': 'Recommended sub-folder'
               }
               
               existing_folders = folder_service.list_folders()
               
               logger.info("  📁 Special Folder Validation:")
               
               for folder, requirement in expected_structure.items():
                   if folder in existing_folders:
                       logger.info(f"    ✓ {folder} - {requirement}")
                   else:
                       if requirement == 'Must exist':
                           logger.error(f"    ❌ {folder} - MISSING ({requirement})")
                       elif requirement == 'Should exist':
                           logger.warning(f"    ⚠ {folder} - MISSING ({requirement})")
                       else:
                           logger.info(f"    ℹ {folder} - Not found ({requirement})")
               
           except Exception as e:
               logger.error(f"Failed to validate special folder structure: {e}")
   
       def cleanup_demo_folders(self, folder_service: IMAPFolderService):
           """
           Clean up demo folders created during the example.
           """
           logger.info("--- Cleaning Up Demo Folders ---")
           
           try:
               # Demo folders to clean up
               demo_folders = [
                   'Demo_Folder',
                   'Processing_Temp',
                   'Archive_Test',
                   'Test & Development',
                   'Reports (Monthly)',
                   'Archive-2024',
                   'Temp_Folder'
               ]
               
               existing_folders = folder_service.list_folders()
               
               for folder in demo_folders:
                   if folder in existing_folders:
                       try:
                           logger.info(f"  🗑 Deleting demo folder: {folder}")
                           
                           result = folder_service.delete_folder(folder)
                           
                           if result.success:
                               logger.info(f"    ✓ Deleted: {folder}")
                           else:
                               logger.warning(f"    ⚠ Failed to delete {folder}: {result.error_message}")
                       
                       except Exception as e:
                           logger.warning(f"    ⚠ Error deleting {folder}: {e}")
               
               # Clean up nested demo folders
               nested_demo_folders = [
                   folder for folder in existing_folders
                   if folder.startswith(('Projects/', 'Categories/', 'Archive/'))
                   and any(demo_part in folder for demo_part in ['Alpha', 'Beta', 'Website_', 'Mobile_'])
               ]
               
               for folder in nested_demo_folders:
                   try:
                       logger.info(f"  🗑 Deleting nested demo folder: {folder}")
                       
                       result = folder_service.delete_folder(folder)
                       
                       if result.success:
                           logger.info(f"    ✓ Deleted: {folder}")
                       else:
                           logger.warning(f"    ⚠ Failed to delete {folder}: {result.error_message}")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Error deleting {folder}: {e}")
               
               logger.info("  ✓ Demo folder cleanup completed")
               
           except Exception as e:
               logger.error(f"Failed to cleanup demo folders: {e}")


   def main():
       """
       Main function to run the folder management example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = FolderManagementExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_folder_operations()
           logger.info("🎉 Folder management example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Folder Operations Reference
---------------------------

Basic Folder Operations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all folders
   folders = folder_service.list_folders()
   
   # Create folder
   result = folder_service.create_folder("New_Folder")
   
   # Delete folder
   result = folder_service.delete_folder("Old_Folder")
   
   # Rename folder
   result = folder_service.rename_folder("Old_Name", "New_Name")

Folder Subscriptions
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List subscribed folders
   subscribed = folder_service.list_subscribed_folders()
   
   # Subscribe to folder
   result = folder_service.subscribe_folder("Folder_Name")
   
   # Unsubscribe from folder
   result = folder_service.unsubscribe_folder("Folder_Name")

Message Operations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Move messages between folders
   result = uid_service.uid_move(message_set, "Target_Folder")
   
   # Copy messages to folder
   result = uid_service.uid_copy(message_set, "Target_Folder")
   
   # Select folder for operations
   result = uid_service.select("Folder_Name")

Folder Organization Patterns
----------------------------

Date-Based Organization
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Yearly structure
   "Archive/2024"
   "Archive/2024/Q1"
   "Archive/2024/Q2"
   "Archive/2024/Q3"
   "Archive/2024/Q4"
   
   # Monthly structure
   "Archive/2024/January"
   "Archive/2024/February"

Project-Based Organization
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Project structure
   "Projects/ProjectName"
   "Projects/ProjectName/Documents"
   "Projects/ProjectName/Meetings"
   "Projects/ProjectName/Reports"

Category-Based Organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Category structure
   "Categories/Work"
   "Categories/Work/Meetings"
   "Categories/Work/Reports"
   "Categories/Personal"
   "Categories/Personal/Finance"

Special Folders
---------------

System Folders
~~~~~~~~~~~~~~

.. code-block:: python

   # Standard system folders
   "INBOX"          # Main inbox
   "Sent"           # Sent messages
   "Drafts"         # Draft messages
   "Trash"          # Deleted messages
   "Spam"           # Spam messages

Recommended Folders
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Recommended additional folders
   "Archive"        # For archiving old messages
   "Important"      # For important messages
   "Processing"     # For messages being processed
   "Backup"         # For backup purposes

Best Practices
--------------

✅ **DO:**

- Use descriptive folder names

- Create logical hierarchies

- Regularly clean up empty folders

- Use consistent naming conventions

- Backup important folders

- Test folder operations in development

❌ **DON'T:**

- Use special characters in folder names

- Create overly deep hierarchies

- Delete system folders

- Ignore folder operation errors

- Create too many folders

- Use spaces in folder names (server-dependent)

Error Handling
--------------

.. code-block:: python

   try:
       result = folder_service.create_folder("New_Folder")
       
       if result.success:
           logger.info("Folder created successfully")
       else:
           logger.error(f"Failed to create folder: {result.error_message}")
           
   except IMAPFolderError as e:
       logger.error(f"Folder operation failed: {e}")
   except Exception as e:
       logger.error(f"Unexpected error: {e}")

Folder Naming Guidelines
------------------------

Good Names
~~~~~~~~~~

.. code-block:: text

   ✓ "Archive_2024"
   ✓ "Projects_Alpha"
   ✓ "Work_Reports"
   ✓ "Personal_Finance"
   ✓ "Temp_Processing"

Avoid
~~~~~

.. code-block:: text

   ❌ "Archive 2024" (spaces)
   ❌ "Projects@Alpha" (special chars)
   ❌ "Work/Reports" (forward slash)
   ❌ "Personal.Finance" (periods)
   ❌ "Temp Processing!" (exclamation)

Server Limitations
------------------

Different servers have different limitations:

- **Gmail**: Labels are folders, limited hierarchy
- **Outlook**: Standard folder support
- **Dovecot**: Full folder support
- **Courier**: Basic folder support

Always test folder operations with your specific server.

Next Steps
----------

For more advanced patterns, see:

- :doc:`mailbox_management` - Mailbox operations
- :doc:`message_set_usage` - Advanced MessageSet usage
- :doc:`large_volume_handling` - Large dataset handling
- :doc:`production_patterns` - Production-ready patterns 