# Enhanced IMAP Mailbox Service Examples

This directory contains comprehensive examples demonstrating the enhanced IMAP mailbox service capabilities in the sage-imap library. The examples showcase advanced features including bulk operations, UID handling, monitoring, and production-ready patterns.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Examples Overview](#examples-overview)
- [Quick Start](#quick-start)
- [Detailed Examples](#detailed-examples)
- [Features Demonstrated](#features-demonstrated)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Integration Examples](#integration-examples)

## 🌟 Overview

The enhanced IMAP mailbox service provides enterprise-grade email management capabilities with:

- **Comprehensive Operations**: Search, fetch, move, delete, restore, and bulk operations
- **UID Support**: Persistent message identification for reliable operations
- **Monitoring**: Performance metrics, error tracking, and operation statistics
- **Validation**: Input validation and error handling for robust operations
- **Batch Processing**: Efficient handling of large message sets
- **Production Ready**: Connection pooling, retry logic, and resilience features

## 🔧 Prerequisites

### System Requirements
- Python 3.7 or higher
- sage-imap library installed
- Valid IMAP server credentials
- Network connectivity to IMAP server

### Installation
```bash
pip install sage-imap
```

### Configuration
Update the connection configuration in examples with your IMAP server details:

```python
config = ConnectionConfig(
    host="your-imap-server.com",
    username="your-username",
    password="your-password",
    enable_monitoring=True,
    timeout=30.0
)
```

## 📚 Examples Overview

### Core Mailbox Examples

| Example | Description | Key Features |
|---------|-------------|--------------|
| `06_mailbox_operations_example.py` | Basic mailbox operations | Select, search, fetch, move, delete, monitoring |
| `07_advanced_mailbox_features.py` | Advanced features | Email upload, analytics, recovery, sent management |
| `08_mailbox_uid_operations.py` | UID-based operations | Persistent identification, synchronization patterns |

### Example Categories

1. **Basic Operations** - Essential mailbox management
2. **Search & Fetch** - Advanced message retrieval
3. **Message Management** - Move, delete, restore operations
4. **Bulk Operations** - Efficient batch processing
5. **UID Operations** - Persistent message handling
6. **Monitoring** - Performance and error tracking
7. **Advanced Features** - Upload, analytics, recovery

## 🚀 Quick Start

### Basic Usage
```python
from sage_imap.services.client import IMAPClient, ConnectionConfig
from sage_imap.services.mailbox import IMAPMailboxService

# Configure connection
config = ConnectionConfig(
    host="your-imap-server.com",
    username="your-username",
    password="your-password",
    enable_monitoring=True
)

# Use mailbox service
with IMAPClient(config) as client:
    mailbox_service = IMAPMailboxService(client)

    # Select mailbox
    result = mailbox_service.select("INBOX")
    if result.success:
        print(f"Selected INBOX: {result.message_count} messages")

    # Search for emails
    from sage_imap.helpers.search import IMAPSearchCriteria
    search_result = mailbox_service.search(IMAPSearchCriteria().unseen())
    print(f"Found {search_result.message_count} unread emails")
```

### Running Examples
```bash
# Run basic operations example
python examples/06_mailbox_operations_example.py

# Run advanced features example
python examples/07_advanced_mailbox_features.py

# Run UID operations example
python examples/08_mailbox_uid_operations.py
```

## 📖 Detailed Examples

### 06_mailbox_operations_example.py

**Purpose**: Demonstrates fundamental mailbox operations and monitoring

**Key Sections**:
- **Basic Operations**: Select, close, status, check operations
- **Search & Fetch**: Email search with criteria and message fetching
- **Message Management**: Move, delete, restore simulations
- **UID Operations**: Comparison with sequence-based operations
- **Bulk Operations**: Batch processing and performance optimization
- **Error Handling**: Validation and error recovery patterns

**Sample Output**:
```
BASIC MAILBOX OPERATIONS
✓ Selected INBOX (execution time: 0.125s)
✓ Mailbox status retrieved (execution time: 0.089s)
✓ Found 42 recent emails
✓ Fetched 3 email headers
```

### 07_advanced_mailbox_features.py

**Purpose**: Showcases advanced features and enterprise capabilities

**Key Sections**:
- **Email Upload**: EML file handling and bulk upload operations
- **Sent Management**: Sent message handling and folder management
- **Advanced Search**: Complex search patterns and criteria
- **Analytics**: Mailbox statistics and performance metrics
- **Recovery**: Message restoration and recovery workflows

**Sample Output**:
```
EMAIL UPLOAD AND EML FILE HANDLING
✓ Created 3 sample emails
✓ Upload simulation completed
✓ Batch processing: 10 batches processed
✓ Performance metrics: 2.3 ops/sec
```

### 08_mailbox_uid_operations.py

**Purpose**: Comprehensive UID-based operations and best practices

**Key Sections**:
- **UID vs Sequence**: Comparison and use case analysis
- **UID Search**: Persistent message identification
- **UID Fetch**: Reliable message retrieval
- **UID Management**: Move, delete, restore with UIDs
- **Best Practices**: Caching, synchronization, error handling

**Sample Output**:
```
UID VS SEQUENCE NUMBER COMPARISON
✓ Regular search: 156 messages (0.234s)
✓ UID search: 156 messages (0.267s)
✓ UID operations provide persistent identification
✓ Recommended for long-running processes
```

## 🎯 Features Demonstrated

### Core Mailbox Operations
- **Selection**: Mailbox selection with validation and monitoring
- **Search**: Advanced search with multiple criteria
- **Fetch**: Message retrieval with different parts (header, body, full)
- **Status**: Mailbox status and statistics
- **Check**: Mailbox consistency checks

### Message Management
- **Move**: Message relocation between folders
- **Delete**: Permanent message deletion
- **Trash**: Safe message deletion to trash folder
- **Restore**: Message recovery from trash
- **Copy**: Message duplication

### Bulk Operations
- **Batch Processing**: Efficient handling of large message sets
- **Progress Monitoring**: Real-time operation progress
- **Error Handling**: Per-message error tracking
- **Performance Optimization**: Configurable batch sizes

### UID Operations
- **Persistent Identification**: Stable message references
- **Synchronization**: Reliable message tracking
- **Cross-Session**: Operations across multiple sessions
- **Conflict Resolution**: Handling of UID conflicts

### Monitoring & Analytics
- **Performance Metrics**: Operation timing and throughput
- **Error Tracking**: Comprehensive error logging
- **Statistics**: Mailbox and operation statistics
- **Health Monitoring**: Service health checks

### Advanced Features
- **Email Upload**: EML file processing and upload
- **Sent Management**: Sent message handling
- **Validation**: Input validation and sanitization
- **Recovery**: Message restoration workflows
- **Integration**: External system integration patterns

## 📋 Best Practices

### Connection Management
```python
# Use context managers for automatic cleanup
with IMAPClient(config) as client:
    mailbox_service = IMAPMailboxService(client)
    # Operations here
    # Automatic cleanup on exit
```

### Error Handling
```python
# Check operation results
result = mailbox_service.select("INBOX")
if result.success:
    # Continue with operations
    pass
else:
    logger.error(f"Operation failed: {result.error_message}")
    # Handle error appropriately
```

### Performance Optimization
```python
# Configure batch sizes for bulk operations
mailbox_service.bulk_operation_batch_size = 50
mailbox_service.max_concurrent_operations = 3

# Use UID operations for persistence
uid_service = IMAPMailboxUIDService(client)
```

### Monitoring Integration
```python
# Monitor operation performance
stats = mailbox_service.get_monitoring_statistics()
print(f"Average search time: {stats['average_times']['search']:.3f}s")
print(f"Error rate: {sum(stats['error_counts'].values())}")
```

## 🔧 Troubleshooting

### Common Issues

**Connection Problems**:
```python
# Check connection status
if not client.is_connected():
    print("Connection lost, attempting reconnection...")
    client.connect()
```

**Mailbox Selection Failures**:
```python
# Validate mailbox name
try:
    result = mailbox_service.select("NonExistentFolder")
    if not result.success:
        print(f"Selection failed: {result.error_message}")
except Exception as e:
    print(f"Validation error: {e}")
```

**Performance Issues**:
```python
# Monitor operation times
stats = mailbox_service.get_monitoring_statistics()
slow_operations = {
    op: time for op, time in stats['average_times'].items()
    if time > 1.0  # Operations taking more than 1 second
}
```

### Debugging Tips

1. **Enable Detailed Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Monitor Operation Statistics**:
```python
stats = mailbox_service.get_monitoring_statistics()
print(f"Total operations: {stats['total_operations']}")
print(f"Error counts: {stats['error_counts']}")
```

3. **Validate Inputs**:
```python
# Use built-in validation
mailbox_service.validator.validate_mailbox("INBOX")
mailbox_service.validator.validate_message_set(msg_set)
```

## 🔗 Integration Examples

### Flask Web Application
```python
from flask import Flask, jsonify
from sage_imap.services.client import IMAPClient
from sage_imap.services.mailbox import IMAPMailboxService

app = Flask(__name__)

@app.route('/mailbox/stats')
def get_mailbox_stats():
    with IMAPClient(config) as client:
        service = IMAPMailboxService(client)
        service.select("INBOX")
        stats = service.get_mailbox_statistics()
        return jsonify({
            'total_messages': stats.total_messages,
            'unread_messages': stats.unread_messages,
            'recent_messages': stats.recent_messages
        })
```

### Celery Task Processing
```python
from celery import Celery
from sage_imap.services.mailbox import IMAPMailboxService

app = Celery('email_processor')

@app.task
def process_emails():
    with IMAPClient(config) as client:
        service = IMAPMailboxService(client)
        service.select("INBOX")

        # Process emails in batches
        result = service.search_and_process(
            criteria=IMAPSearchCriteria().unseen(),
            processor_func=process_single_email,
            batch_size=10
        )

        return {
            'processed': result.successful_messages,
            'failed': result.failed_messages,
            'execution_time': result.execution_time
        }
```

### Monitoring Dashboard
```python
import json
from datetime import datetime

def export_metrics():
    with IMAPClient(config) as client:
        service = IMAPMailboxService(client)
        stats = service.get_monitoring_statistics()

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'operations': stats['operations_by_type'],
            'errors': stats['error_counts'],
            'performance': stats['average_times']
        }

        return json.dumps(metrics, indent=2)
```

## 📊 Performance Benchmarks

### Typical Performance Metrics

| Operation | Average Time | Throughput | Notes |
|-----------|--------------|------------|-------|
| Select | 0.1s | N/A | Depends on mailbox size |
| Search (All) | 0.3s | 500 msgs/s | Server-dependent |
| Fetch (Header) | 0.05s | 20 msgs/s | Per message |
| Fetch (Full) | 0.2s | 5 msgs/s | Per message |
| Move | 0.1s | 10 msgs/s | Per message |
| Bulk Upload | 0.01s | 100 msgs/s | Per message in batch |

### Optimization Recommendations

1. **Use Batch Operations**: Process multiple messages together
2. **Optimize Search Criteria**: Use specific criteria to reduce result sets
3. **Cache Results**: Store frequently accessed data
4. **Monitor Performance**: Track operation times and optimize bottlenecks
5. **Use UID Operations**: For persistent operations and synchronization

## 📝 Contributing

To contribute to the mailbox examples:

1. Follow the existing code style and patterns
2. Add comprehensive error handling
3. Include monitoring and logging
4. Provide detailed documentation
5. Test with various IMAP servers
6. Update this README with new examples

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section above
- Review the detailed examples
- Monitor operation statistics for debugging
- Enable detailed logging for diagnosis

---

*These examples demonstrate the full capabilities of the enhanced IMAP mailbox service. Use them as a foundation for building robust email management applications.*
