# Enhanced IMAPClient Examples

This directory contains comprehensive examples demonstrating all the advanced features and capabilities of the enhanced IMAPClient from the python-sage-imap library.

## Overview

The enhanced IMAPClient provides production-ready IMAP functionality with advanced features including:

- **Connection Pooling**: Efficient connection reuse and management
- **Retry Logic**: Automatic retry with exponential backoff
- **Health Monitoring**: Real-time connection health tracking
- **Metrics Collection**: Comprehensive performance and usage metrics
- **Resilience Features**: Network interruption handling and recovery
- **Advanced Configuration**: Environment-specific settings and customization

## Examples Structure

### 1. Basic Client Usage (`01_basic_client_usage.py`)

**Purpose**: Demonstrates fundamental IMAPClient usage patterns

**Features Covered**:
- Basic connection establishment
- Context manager usage
- Configuration objects
- Error handling patterns
- Metrics and monitoring basics
- Temporary connections

**Key Concepts**:
```python
# Basic connection
client = IMAPClient(host, username, password)
client.connect()

# Context manager (recommended)
with IMAPClient(host, username, password) as client:
    status, data = client.select("INBOX")

# Advanced configuration
config = ConnectionConfig(
    host=host,
    username=username,
    password=password,
    max_retries=5,
    retry_delay=2.0,
    enable_monitoring=True
)
client = IMAPClient.from_config(config)
```

### 2. Connection Pooling (`02_connection_pooling_example.py`)

**Purpose**: Demonstrates connection pooling for improved performance

**Features Covered**:
- Basic pooling setup
- Concurrent connection usage
- Pool configuration and management
- Performance comparison
- Pool monitoring and statistics

**Key Concepts**:
```python
# Enable connection pooling
client = IMAPClient(host, username, password, use_pool=True)

# Pool statistics
stats = get_pool_stats()
print(f"Pooled connections: {stats['total_pooled_connections']}")

# Clear pool when needed
clear_connection_pool()
```

### 3. Retry Logic and Resilience (`03_retry_and_resilience_example.py`)

**Purpose**: Demonstrates retry mechanisms and network resilience

**Features Covered**:
- Automatic retry with exponential backoff
- Custom retry decorators
- Network interruption handling
- Health monitoring and recovery
- Connection recovery mechanisms
- Stress testing
- Timeout handling

**Key Concepts**:
```python
# Retry configuration
config = ConnectionConfig(
    max_retries=3,
    retry_delay=1.0,
    retry_exponential_backoff=True,
    max_retry_delay=10.0
)

# Custom retry decorator
@retry_on_failure(max_retries=3, delay=1.0)
def my_operation():
    # Operation that might fail
    pass

# Health monitoring
health = client.health_check()
if not health["is_connected"]:
    client.connect()  # Automatic reconnection
```

### 4. Monitoring and Metrics (`04_monitoring_and_metrics_example.py`)

**Purpose**: Demonstrates comprehensive monitoring and metrics collection

**Features Covered**:
- Basic metrics collection
- Performance monitoring and analysis
- Health monitoring with alerting
- Metrics export (JSON, Prometheus)
- Real-time monitoring dashboard
- Trend analysis

**Key Concepts**:
```python
# Enable monitoring
config = ConnectionConfig(
    enable_monitoring=True,
    health_check_interval=60.0
)

# Get metrics
metrics = client.get_metrics()
print(f"Total operations: {metrics.total_operations}")
print(f"Success rate: {metrics.success_rate}")

# Health check
health = client.health_check()
print(f"Connected: {health['is_connected']}")
print(f"Response time: {health['average_response_time']}")

# Export metrics
export_data = {
    "metrics": asdict(metrics),
    "health": health,
    "timestamp": datetime.now().isoformat()
}
```

### 5. Advanced Client Features (`05_advanced_client_features.py`)

**Purpose**: Demonstrates advanced features and integration patterns

**Features Covered**:
- Environment-specific configurations
- Custom decorators and middleware
- Connection lifecycle management
- Integration with external systems
- Production-ready patterns
- Circuit breaker implementation

**Key Concepts**:
```python
# Environment configurations
prod_config = ClientConfiguration.for_production(host, username, password)
dev_config = ClientConfiguration.for_development(host, username, password)

# Custom decorators
@operation_timing_decorator("my_operation")
@retry_on_failure(max_retries=2)
def my_operation(client):
    return client.list()

# Production service
class ProductionIMAPService:
    def __init__(self, config):
        self.manager = IMAPClientManager(config)
    
    def execute_with_circuit_breaker(self, operation, name):
        # Circuit breaker implementation
        pass
```

## Prerequisites

Before running the examples, ensure you have:

1. **Python 3.8+** installed
2. **python-sage-imap** library installed
3. **Valid IMAP credentials** (Gmail, Outlook, etc.)

## Setup Instructions

1. **Install Dependencies**:
```bash
pip install python-sage-imap
```

2. **Configure Credentials**:
   - Edit each example file
   - Replace placeholder credentials:
     ```python
     HOST = "imap.gmail.com"  # Your IMAP server
     USERNAME = "your_email@gmail.com"  # Your email
     PASSWORD = "your_password"  # Your password or app password
     ```

3. **Gmail Setup** (if using Gmail):
   - Enable 2-factor authentication
   - Generate an app password
   - Use the app password instead of your regular password

## Running Examples

### Individual Examples
```bash
# Run a specific example
python examples/01_basic_client_usage.py

# Run with debug logging
PYTHONPATH=. python -m examples.01_basic_client_usage
```

### All Examples
```bash
# Run all examples in sequence
for example in examples/*.py; do
    echo "Running $example..."
    python "$example"
    echo "---"
done
```

## Common Configuration Options

### Basic Configuration
```python
client = IMAPClient(
    host="imap.gmail.com",
    username="user@gmail.com",
    password="password",
    port=993,
    use_ssl=True,
    timeout=30.0
)
```

### Advanced Configuration
```python
config = ConnectionConfig(
    host="imap.gmail.com",
    username="user@gmail.com",
    password="password",
    port=993,
    use_ssl=True,
    timeout=30.0,
    max_retries=3,
    retry_delay=1.0,
    retry_exponential_backoff=True,
    max_retry_delay=30.0,
    keepalive_interval=300.0,
    health_check_interval=60.0,
    enable_monitoring=True
)
```

## Best Practices

### 1. Always Use Context Managers
```python
# Good
with IMAPClient(host, username, password) as client:
    # Operations here

# Avoid
client = IMAPClient(host, username, password)
client.connect()
# ... operations ...
client.disconnect()  # Easy to forget!
```

### 2. Enable Connection Pooling for Multiple Operations
```python
# For applications with multiple IMAP operations
client = IMAPClient(host, username, password, use_pool=True)
```

### 3. Configure Appropriate Timeouts
```python
# For slow networks
config = ConnectionConfig(
    timeout=60.0,
    max_retries=5,
    retry_delay=2.0
)

# For fast networks
config = ConnectionConfig(
    timeout=15.0,
    max_retries=3,
    retry_delay=0.5
)
```

### 4. Monitor Production Applications
```python
config = ConnectionConfig(
    enable_monitoring=True,
    health_check_interval=30.0
)

# Regular health checks
health = client.health_check()
if health["success_rate"] < 90:
    # Alert or take action
    pass
```

### 5. Handle Errors Gracefully
```python
try:
    with IMAPClient(host, username, password) as client:
        status, data = client.select("INBOX")
except IMAPConnectionError as e:
    logger.error(f"Connection failed: {e}")
    # Implement fallback or retry logic
except IMAPAuthenticationError as e:
    logger.error(f"Authentication failed: {e}")
    # Check credentials
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # General error handling
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify credentials are correct
   - For Gmail: Use app passwords, not regular passwords
   - Check if 2FA is enabled

2. **Connection Timeouts**:
   - Increase timeout values
   - Check network connectivity
   - Verify IMAP server settings

3. **SSL/TLS Issues**:
   - Ensure `use_ssl=True` for secure connections
   - Check if server supports SSL/TLS
   - Verify port numbers (993 for SSL, 143 for non-SSL)

### Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('sage_imap')
logger.setLevel(logging.DEBUG)
```

### Performance Issues
```python
# Enable monitoring to identify bottlenecks
config = ConnectionConfig(enable_monitoring=True)
client = IMAPClient.from_config(config)

# Check metrics
metrics = client.get_metrics()
print(f"Average response time: {metrics.average_response_time}")
print(f"Failed operations: {metrics.failed_operations}")
```

## Integration Examples

### With Flask Web Application
```python
from flask import Flask
from sage_imap.services.client import IMAPClient

app = Flask(__name__)

@app.route('/inbox-count')
def get_inbox_count():
    with IMAPClient(host, username, password) as client:
        status, data = client.select("INBOX")
        return {"count": int(data[0])}
```

### With Celery Background Tasks
```python
from celery import Celery
from sage_imap.services.client import IMAPClient

app = Celery('email_processor')

@app.task
def process_emails():
    with IMAPClient(host, username, password, use_pool=True) as client:
        # Process emails in background
        pass
```

### With Monitoring Systems
```python
# Export metrics to Prometheus
def export_metrics():
    metrics = client.get_metrics()
    prometheus_metrics = [
        f"imap_operations_total {metrics.total_operations}",
        f"imap_response_time_seconds {metrics.average_response_time}",
    ]
    return "\n".join(prometheus_metrics)
```

## Contributing

To add new examples:

1. Follow the existing naming convention: `NN_feature_name_example.py`
2. Include comprehensive docstrings and comments
3. Add error handling and logging
4. Update this README with the new example
5. Test with different IMAP servers

## Support

For issues or questions:

1. Check the main library documentation
2. Review the example code and comments
3. Enable debug logging for troubleshooting
4. Submit issues to the project repository

---

**Note**: Remember to never commit real credentials to version control. Use environment variables or configuration files that are excluded from git. 