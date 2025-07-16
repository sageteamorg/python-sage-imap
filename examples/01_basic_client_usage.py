#!/usr/bin/env python3
"""
Basic IMAPClient Usage Example

This example demonstrates the fundamental usage patterns of the enhanced IMAPClient
including connection management, basic operations, and error handling.

Author: Python Sage IMAP Library
License: MIT
"""

import logging
import time
from datetime import datetime
from typing import Optional

from sage_imap.services.client import IMAPClient, ConnectionConfig
from sage_imap.exceptions import IMAPConnectionError, IMAPAuthenticationError

# Configure logging to see detailed information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def basic_connection_example():
    """
    Demonstrates basic connection establishment and management.
    
    This example shows:
    - Creating an IMAPClient instance
    - Establishing a connection
    - Checking connection status
    - Performing basic operations
    - Proper cleanup
    """
    print("=" * 60)
    print("BASIC CONNECTION EXAMPLE")
    print("=" * 60)
    
    # Configuration - Replace with your actual credentials
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    # Create client instance
    client = IMAPClient(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
        port=993,
        use_ssl=True,
        timeout=30.0
    )
    
    try:
        # Establish connection
        print("Connecting to IMAP server...")
        connection = client.connect()
        print(f"✓ Connected successfully to {HOST}")
        
        # Check connection status
        if client.is_connected():
            print("✓ Connection is healthy")
        
        # Perform basic operations
        print("\nPerforming basic operations:")
        
        # List mailboxes
        status, mailboxes = client.list()
        if status == "OK":
            print(f"✓ Found {len(mailboxes)} mailboxes")
            for mailbox in mailboxes[:5]:  # Show first 5
                print(f"  - {mailbox}")
        
        # Select INBOX
        status, data = client.select("INBOX")
        if status == "OK":
            message_count = int(data[0])
            print(f"✓ Selected INBOX with {message_count} messages")
        
        # Get server capabilities
        capabilities = client.capabilities
        print(f"✓ Server capabilities: {', '.join(capabilities[:5])}...")
        
    except IMAPConnectionError as e:
        print(f"✗ Connection failed: {e}")
    except IMAPAuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    finally:
        # Always disconnect
        client.disconnect()
        print("✓ Disconnected from server")


def context_manager_example():
    """
    Demonstrates using IMAPClient as a context manager.
    
    This example shows:
    - Using 'with' statement for automatic cleanup
    - Exception handling within context
    - Automatic connection and disconnection
    """
    print("\n" + "=" * 60)
    print("CONTEXT MANAGER EXAMPLE")
    print("=" * 60)
    
    # Configuration
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    try:
        # Using context manager - automatic connect/disconnect
        with IMAPClient(HOST, USERNAME, PASSWORD) as client:
            print("✓ Connected using context manager")
            
            # Check connection health
            health = client.health_check()
            print(f"✓ Connection health: {health['is_connected']}")
            print(f"  - Total operations: {health['total_operations']}")
            print(f"  - Success rate: {health['success_rate']:.1f}%")
            
            # Perform operations
            status, data = client.select("INBOX")
            if status == "OK":
                print(f"✓ Selected INBOX with {data[0]} messages")
            
            # Connection automatically closed when exiting 'with' block
            
    except Exception as e:
        print(f"✗ Error in context manager: {e}")
    
    print("✓ Context manager automatically handled cleanup")


def configuration_object_example():
    """
    Demonstrates using ConnectionConfig for advanced configuration.
    
    This example shows:
    - Creating a ConnectionConfig object
    - Setting advanced connection parameters
    - Using configuration with IMAPClient
    - Accessing configuration details
    """
    print("\n" + "=" * 60)
    print("CONFIGURATION OBJECT EXAMPLE")
    print("=" * 60)
    
    # Create advanced configuration
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        port=993,
        use_ssl=True,
        timeout=45.0,
        max_retries=5,
        retry_delay=2.0,
        retry_exponential_backoff=True,
        max_retry_delay=30.0,
        keepalive_interval=300.0,
        health_check_interval=60.0,
        enable_monitoring=True
    )
    
    print("Configuration created with advanced settings:")
    print(f"  - Host: {config.host}")
    print(f"  - Port: {config.port}")
    print(f"  - SSL: {config.use_ssl}")
    print(f"  - Timeout: {config.timeout}s")
    print(f"  - Max retries: {config.max_retries}")
    print(f"  - Retry delay: {config.retry_delay}s")
    print(f"  - Exponential backoff: {config.retry_exponential_backoff}")
    print(f"  - Health check interval: {config.health_check_interval}s")
    print(f"  - Monitoring enabled: {config.enable_monitoring}")
    
    try:
        # Create client from configuration
        client = IMAPClient.from_config(config)
        print("✓ Client created from configuration")
        
        with client:
            print("✓ Connected with advanced configuration")
            
            # Show that configuration is accessible
            print(f"✓ Client config host: {client.config.host}")
            print(f"✓ Client config max_retries: {client.config.max_retries}")
            
    except Exception as e:
        print(f"✗ Configuration example failed: {e}")


def error_handling_example():
    """
    Demonstrates comprehensive error handling patterns.
    
    This example shows:
    - Handling connection errors
    - Handling authentication errors
    - Handling timeout errors
    - Graceful degradation
    - Retry mechanisms
    """
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLE")
    print("=" * 60)
    
    # Test with invalid credentials to demonstrate error handling
    invalid_configs = [
        {
            "name": "Invalid hostname",
            "host": "invalid.hostname.example",
            "username": "test@example.com",
            "password": "password"
        },
        {
            "name": "Invalid credentials",
            "host": "imap.gmail.com",
            "username": "invalid@example.com",
            "password": "wrongpassword"
        },
        {
            "name": "Invalid port",
            "host": "imap.gmail.com",
            "username": "test@example.com",
            "password": "password",
            "port": 12345
        }
    ]
    
    for config_info in invalid_configs:
        print(f"\nTesting: {config_info['name']}")
        
        client = IMAPClient(
            host=config_info["host"],
            username=config_info["username"],
            password=config_info["password"],
            port=config_info.get("port", 993),
            timeout=10.0,  # Short timeout for demo
            max_retries=2   # Fewer retries for demo
        )
        
        try:
            client.connect()
            print("✓ Connection successful (unexpected)")
        except IMAPConnectionError as e:
            print(f"✗ Connection error (expected): {e}")
        except IMAPAuthenticationError as e:
            print(f"✗ Authentication error (expected): {e}")
        except Exception as e:
            print(f"✗ Other error: {e}")
        finally:
            client.disconnect()


def metrics_and_monitoring_example():
    """
    Demonstrates connection metrics and monitoring features.
    
    This example shows:
    - Accessing connection metrics
    - Monitoring connection health
    - Performance tracking
    - Operation statistics
    """
    print("\n" + "=" * 60)
    print("METRICS AND MONITORING EXAMPLE")
    print("=" * 60)
    
    # Note: Replace with valid credentials for actual testing
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    # Create client with monitoring enabled
    client = IMAPClient(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
        max_retries=3,
        enable_monitoring=True  # This would be in ConnectionConfig
    )
    
    try:
        # Connect and perform operations
        print("Connecting and performing monitored operations...")
        client.connect()
        
        # Perform several operations to generate metrics
        operations = [
            lambda: client.list(),
            lambda: client.select("INBOX"),
            lambda: client.noop(),
            lambda: client.status("INBOX", "(MESSAGES RECENT)"),
        ]
        
        for i, operation in enumerate(operations, 1):
            try:
                start_time = time.time()
                operation()
                end_time = time.time()
                print(f"✓ Operation {i} completed in {end_time - start_time:.3f}s")
            except Exception as e:
                print(f"✗ Operation {i} failed: {e}")
        
        # Get and display metrics
        metrics = client.get_metrics()
        print(f"\nConnection Metrics:")
        print(f"  - Connection attempts: {metrics.connection_attempts}")
        print(f"  - Successful connections: {metrics.successful_connections}")
        print(f"  - Failed connections: {metrics.failed_connections}")
        print(f"  - Total operations: {metrics.total_operations}")
        print(f"  - Failed operations: {metrics.failed_operations}")
        print(f"  - Average response time: {metrics.average_response_time:.3f}s")
        print(f"  - Last connection: {metrics.last_connection_time}")
        
        if metrics.total_operations > 0:
            success_rate = ((metrics.total_operations - metrics.failed_operations) / 
                          metrics.total_operations * 100)
            print(f"  - Success rate: {success_rate:.1f}%")
        
        # Perform health check
        health = client.health_check()
        print(f"\nHealth Check Results:")
        print(f"  - Is connected: {health['is_connected']}")
        print(f"  - Connection age: {health['connection_age']:.1f}s")
        print(f"  - Success rate: {health['success_rate']:.1f}%")
        print(f"  - Average response time: {health['average_response_time']:.3f}s")
        
    except Exception as e:
        print(f"✗ Monitoring example failed: {e}")
        # Show metrics even on failure
        metrics = client.get_metrics()
        if metrics.last_error:
            print(f"Last error: {metrics.last_error}")
    finally:
        client.disconnect()


def temporary_connection_example():
    """
    Demonstrates temporary connection management.
    
    This example shows:
    - Using temporary_connection context manager
    - Efficient connection reuse
    - Automatic connection management
    """
    print("\n" + "=" * 60)
    print("TEMPORARY CONNECTION EXAMPLE")
    print("=" * 60)
    
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    client = IMAPClient(HOST, USERNAME, PASSWORD)
    
    try:
        # First temporary connection
        print("Using first temporary connection...")
        with client.temporary_connection() as conn:
            status, data = conn.select("INBOX")
            print(f"✓ First connection - INBOX has {data[0]} messages")
        
        print("✓ First temporary connection closed")
        
        # Second temporary connection (will reuse if still connected)
        print("Using second temporary connection...")
        with client.temporary_connection() as conn:
            status, mailboxes = conn.list()
            print(f"✓ Second connection - Found {len(mailboxes)} mailboxes")
        
        print("✓ Second temporary connection closed")
        
    except Exception as e:
        print(f"✗ Temporary connection example failed: {e}")
    finally:
        client.disconnect()


def main():
    """
    Main function to run all examples.
    
    This function demonstrates the complete usage patterns of the enhanced
    IMAPClient with comprehensive examples of all features.
    """
    print("Enhanced IMAPClient Examples")
    print("=" * 60)
    print("This script demonstrates various usage patterns of the enhanced IMAPClient.")
    print("Note: Update the credentials in each example before running.")
    print()
    
    # Run all examples
    examples = [
        basic_connection_example,
        context_manager_example,
        configuration_object_example,
        error_handling_example,
        metrics_and_monitoring_example,
        temporary_connection_example,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Example {example.__name__} failed: {e}")
        
        # Small delay between examples
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main() 