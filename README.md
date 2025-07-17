# Python Sage IMAP

[![PyPI version](https://badge.fury.io/py/python-sage-imap.svg)](https://badge.fury.io/py/python-sage-imap)
[![Python](https://img.shields.io/pypi/pyversions/python-sage-imap.svg)](https://pypi.org/project/python-sage-imap/)
[![Downloads](https://pepy.tech/badge/python-sage-imap)](https://pepy.tech/project/python-sage-imap)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/sageteamorg/python-sage-imap/graph/badge.svg?token=I10LGK910X)](https://codecov.io/gh/sageteamorg/python-sage-imap)
[![Documentation](https://readthedocs.org/projects/python-sage-imap/badge/?version=latest)](https://python-sage-imap.readthedocs.io/en/latest/)

**A robust, production-ready Python library for IMAP email operations with advanced features including connection pooling, retry logic, monitoring, and comprehensive email management.**

## 🚀 Why Python Sage IMAP?

Python Sage IMAP is designed for developers who need reliable, scalable email processing capabilities. Unlike basic IMAP libraries, it provides enterprise-grade features that handle real-world challenges like connection management, error recovery, and performance monitoring.

### 🎯 Key Features

- **🔄 Connection Management**: Advanced connection pooling with automatic retry logic
- **📊 Monitoring & Metrics**: Built-in performance tracking and operation statistics
- **🔍 Advanced Search**: Powerful email search with multiple criteria and filters
- **📁 Folder Operations**: Complete folder management (create, rename, delete, list)
- **🏷️ Flag Management**: Comprehensive flag operations with bulk support
- **📧 Email Processing**: Rich email parsing with attachment handling
- **🔐 Security**: SSL/TLS support with secure authentication
- **⚡ Performance**: Optimized for handling large mailboxes efficiently
- **🛡️ Error Handling**: Comprehensive exception handling and recovery
- **🎨 Modern API**: Clean, intuitive interface with type hints

## 📦 Installation

```bash
pip install python-sage-imap
```

### Requirements

- Python 3.7+
- IMAP server access
- SSL/TLS support (recommended)

## 🏃 Quick Start

### Basic Connection and Operations

```python
from sage_imap.services import IMAPClient, IMAPMailboxService
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet

# Connect to IMAP server
with IMAPClient(
    host="imap.example.com",
    username="user@example.com", 
    password="your_password"
) as client:
    # Get server capabilities
    capabilities = client.capability()
    print(f"Server capabilities: {capabilities}")
    
    # Select mailbox
    status, messages = client.select("INBOX")
    print(f"Selected INBOX: {status}, Messages: {messages}")
    
    # Search for emails
    with IMAPMailboxService(client) as mailbox:
        # Search for recent emails
        result = mailbox.search(IMAPSearchCriteria.recent(days=7))
        if result.success:
            print(f"Found {result.message_count} recent emails")
```

### Advanced Usage with Connection Pooling

```python
from sage_imap.services import IMAPClient, ConnectionConfig
from sage_imap.services import IMAPFolderService, IMAPMailboxService

# Advanced configuration
config = ConnectionConfig(
    host="imap.example.com",
    username="user@example.com",
    password="your_password",
    port=993,
    use_ssl=True,
    timeout=30.0,
    max_retries=3,
    retry_delay=1.0
)

# Create client with pooling
client = IMAPClient.from_config(config)

try:
    with client:
        # Folder operations
        folder_service = IMAPFolderService(client)
        
        # Create folder hierarchy
        folder_service.create_folder("Projects/Work")
        folder_service.create_folder("Projects/Personal")
        
        # List all folders
        folders = folder_service.list_folders()
        for folder in folders:
            print(f"Folder: {folder.name}, Messages: {folder.message_count}")
        
        # Mailbox operations
        with IMAPMailboxService(client) as mailbox:
            mailbox.select("INBOX")
            
            # Search with complex criteria
            criteria = IMAPSearchCriteria.and_criteria(
                IMAPSearchCriteria.from_address("boss@company.com"),
                IMAPSearchCriteria.subject("Important"),
                IMAPSearchCriteria.unseen()
            )
            
            result = mailbox.search(criteria)
            if result.success:
                print(f"Found {result.message_count} important unread emails")
                
                # Move important emails to priority folder
                if result.affected_messages:
                    msg_set = MessageSet(result.affected_messages)
                    move_result = mailbox.move(msg_set, "INBOX/Priority")
                    print(f"Moved {move_result.message_count} emails")

finally:
    # Get metrics
    metrics = client.get_metrics()
    print(f"Total operations: {metrics.total_operations}")
    print(f"Success rate: {metrics.successful_connections/metrics.connection_attempts:.2%}")
```

## 📚 Comprehensive Examples

### 1. Email Search and Processing

```python
from sage_imap.services import IMAPClient, IMAPMailboxService
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.enums import MessagePart
from sage_imap.models.message import MessageSet

with IMAPClient("imap.example.com", "user@example.com", "password") as client:
    with IMAPMailboxService(client) as mailbox:
        mailbox.select("INBOX")
        
        # Search for emails from specific sender
        search_result = mailbox.search(
            IMAPSearchCriteria.from_address("notifications@github.com")
        )
        
        if search_result.success and search_result.affected_messages:
            msg_set = MessageSet(search_result.affected_messages[:10])  # First 10 messages
            
            # Fetch email headers
            emails = mailbox.fetch(msg_set, MessagePart.BODY_HEADER_FIELDS)
            
            for email in emails:
                print(f"Subject: {email.subject}")
                print(f"From: {email.from_address}")
                print(f"Date: {email.date}")
                print("-" * 50)
```

### 2. Folder Management

```python
from sage_imap.services import IMAPClient, IMAPFolderService
from sage_imap.helpers.enums import DefaultMailboxes

with IMAPClient("imap.example.com", "user@example.com", "password") as client:
    folder_service = IMAPFolderService(client)
    
    # Create organized folder structure
    project_folders = ["Projects/Client-A", "Projects/Client-B", "Projects/Internal"]
    
    for folder in project_folders:
        result = folder_service.create_folder(folder)
        print(f"Created {folder}: {result.success}")
    
    # List folder hierarchy
    hierarchy = folder_service.get_folder_hierarchy()
    print("Folder structure:")
    for parent, children in hierarchy.items():
        print(f"  {parent}/")
        for child in children:
            print(f"    {child}")
    
    # Get folder statistics
    stats = folder_service.get_folder_statistics()
    print(f"Total folders: {stats['total_folders']}")
    print(f"Recent operations: {stats['recent_operations']}")
```

### 3. Flag Management

```python
from sage_imap.services import IMAPClient, IMAPMailboxService, IMAPFlagService
from sage_imap.helpers.enums import Flag
from sage_imap.models.message import MessageSet

with IMAPClient("imap.example.com", "user@example.com", "password") as client:
    with IMAPMailboxService(client) as mailbox:
        mailbox.select("INBOX")
        
        # Get important emails
        search_result = mailbox.search(
            IMAPSearchCriteria.subject("URGENT")
        )
        
        if search_result.success:
            flag_service = IMAPFlagService(mailbox)
            msg_set = MessageSet(search_result.affected_messages)
            
            # Mark as important and read
            flag_service.bulk_add_flags(msg_set, [Flag.FLAGGED, Flag.SEEN])
            
            # Get flag statistics
            stats = flag_service.get_operation_statistics()
            print(f"Flag operations: {stats['total_operations']}")
            print(f"Success rate: {stats['success_rate']:.2%}")
```

### 4. Email Backup and Migration

```python
from sage_imap.services import IMAPClient, IMAPMailboxService
from sage_imap.helpers.enums import MessagePart
from sage_imap.models.message import MessageSet
from sage_imap.utils import read_eml_files_from_directory

# Source server
source_config = {
    "host": "old-server.example.com",
    "username": "user@example.com",
    "password": "old_password"
}

# Destination server
dest_config = {
    "host": "new-server.example.com",
    "username": "user@example.com", 
    "password": "new_password"
}

# Backup emails from source
with IMAPClient(**source_config) as source_client:
    with IMAPMailboxService(source_client) as source_mailbox:
        source_mailbox.select("INBOX")
        
        # Get all emails
        search_result = source_mailbox.search(IMAPSearchCriteria.ALL)
        if search_result.success:
            msg_set = MessageSet(search_result.affected_messages)
            
            # Fetch full emails
            emails = source_mailbox.fetch(msg_set, MessagePart.RFC822)
            
            # Upload to destination server
            with IMAPClient(**dest_config) as dest_client:
                with IMAPMailboxService(dest_client) as dest_mailbox:
                    dest_mailbox.select("INBOX")
                    
                    # Upload emails with original flags
                    upload_result = dest_mailbox.upload_eml(
                        emails, 
                        flags=None,  # Preserve original flags
                        mailbox="INBOX"
                    )
                    
                    print(f"Migrated {upload_result.message_count} emails")
```

## 🔧 Advanced Configuration

### Connection Configuration

```python
from sage_imap.services import ConnectionConfig, IMAPClient

# Production configuration
config = ConnectionConfig(
    host="imap.example.com",
    username="user@example.com",
    password="secure_password",
    port=993,
    use_ssl=True,
    timeout=30.0,
    max_retries=5,
    retry_delay=2.0,
    enable_monitoring=True,
    pool_size=10,
    pool_timeout=300
)

# Use configuration
client = IMAPClient.from_config(config)
```

### Monitoring and Metrics

```python
from sage_imap.services import IMAPClient

with IMAPClient("imap.example.com", "user@example.com", "password") as client:
    # Perform operations...
    
    # Get detailed metrics
    metrics = client.get_metrics()
    print(f"Connection attempts: {metrics.connection_attempts}")
    print(f"Successful connections: {metrics.successful_connections}")
    print(f"Failed connections: {metrics.failed_connections}")
    print(f"Average response time: {metrics.average_response_time:.2f}s")
    print(f"Total operations: {metrics.total_operations}")
    print(f"Failed operations: {metrics.failed_operations}")
    
    # Reset metrics if needed
    client.reset_metrics()
```

## 📖 API Reference

### Core Classes

#### IMAPClient
- **Purpose**: Main client for IMAP server connection and management
- **Features**: Connection pooling, retry logic, metrics, health checks
- **Usage**: Context manager or manual connection management

#### IMAPMailboxService  
- **Purpose**: Email operations (search, fetch, move, delete)
- **Features**: Bulk operations, UID support, validation
- **Usage**: Context manager for automatic mailbox management

#### IMAPFolderService
- **Purpose**: Folder operations (create, rename, delete, list)
- **Features**: Hierarchy management, validation, statistics
- **Usage**: Direct instantiation with client

#### IMAPFlagService
- **Purpose**: Email flag management (read, important, etc.)
- **Features**: Bulk operations, flag synchronization
- **Usage**: Instantiation with mailbox service

### Helper Classes

#### IMAPSearchCriteria
- **Purpose**: Building complex search queries
- **Features**: Logical operators, date ranges, text searches
- **Usage**: Static methods for criteria building

#### MessageSet
- **Purpose**: Representing sets of email messages
- **Features**: Range support, validation, conversion
- **Usage**: Create from lists or strings

## 🛠️ Error Handling

```python
from sage_imap.services import IMAPClient
from sage_imap.exceptions import (
    IMAPConnectionError,
    IMAPAuthenticationError,
    IMAPMailboxSelectionError,
    IMAPSearchError
)

try:
    with IMAPClient("imap.example.com", "user@example.com", "password") as client:
        # Your operations here
        pass
        
except IMAPConnectionError as e:
    print(f"Connection failed: {e}")
except IMAPAuthenticationError as e:
    print(f"Authentication failed: {e}")
except IMAPMailboxSelectionError as e:
    print(f"Mailbox selection failed: {e}")
except IMAPSearchError as e:
    print(f"Search operation failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=sage_imap --cov-report=html

# Run specific test categories
python -m pytest tests/services/  # Service tests
python -m pytest tests/helpers/   # Helper tests
python -m pytest tests/models/    # Model tests
```

## 📊 Performance Tips

1. **Use Connection Pooling**: Enable pooling for multiple operations
2. **Batch Operations**: Process messages in batches for better performance
3. **UID Operations**: Use UID-based operations for persistence
4. **Selective Fetching**: Fetch only required message parts
5. **Monitor Metrics**: Track performance and optimize accordingly

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/sageteamorg/python-sage-imap.git
cd python-sage-imap

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run linting
python -m black sage_imap/
python -m isort sage_imap/
python -m flake8 sage_imap/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ by the [SAGE Team](https://github.com/sageteamorg)
- Inspired by the need for robust email processing in Python
- Thanks to all contributors and users of the library

## 📞 Support

- 📖 [Documentation](https://python-sage-imap.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/sageteamorg/python-sage-imap/issues)
- 💬 [Discussions](https://github.com/sageteamorg/python-sage-imap/discussions)
- 📧 [Email Support](mailto:support@sageteam.org)

---

**Keywords**: IMAP, email, Python, mail client, email processing, IMAP client, email management, Python email library, IMAP library, email automation, mail server, email operations, IMAP protocol, email parsing, attachment handling, email search, folder management, flag management, email backup, email migration, production email, enterprise email, email monitoring, email metrics, connection pooling, retry logic, email validation, SSL email, TLS email, secure email, email authentication, email reliability, email performance, bulk email operations, email synchronization, email utilities, email tools, email SDK, email API, email framework, email service, email solution
