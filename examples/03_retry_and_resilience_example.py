#!/usr/bin/env python3
"""
Retry Logic and Resilience Example

This example demonstrates the advanced retry logic and resilience features of the
enhanced IMAPClient including exponential backoff, health monitoring, and automatic
recovery mechanisms.

Author: Python Sage IMAP Library
License: MIT
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from sage_imap.services.client import IMAPClient, ConnectionConfig, retry_on_failure
from sage_imap.exceptions import IMAPConnectionError, IMAPAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def basic_retry_example():
    """
    Demonstrates basic retry functionality with exponential backoff.
    
    This example shows:
    - Automatic retry on connection failures
    - Exponential backoff delay
    - Retry limit configuration
    - Success after retries
    """
    print("=" * 60)
    print("BASIC RETRY EXAMPLE")
    print("=" * 60)
    
    # Configuration with retry settings
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        max_retries=3,
        retry_delay=1.0,
        retry_exponential_backoff=True,
        max_retry_delay=10.0,
        timeout=15.0
    )
    
    print("Configuration:")
    print(f"  - Max retries: {config.max_retries}")
    print(f"  - Initial retry delay: {config.retry_delay}s")
    print(f"  - Exponential backoff: {config.retry_exponential_backoff}")
    print(f"  - Max retry delay: {config.max_retry_delay}s")
    print(f"  - Timeout: {config.timeout}s")
    
    client = IMAPClient.from_config(config)
    
    try:
        print("\nAttempting connection with retry logic...")
        start_time = time.time()
        
        # This will automatically retry on failure
        client.connect()
        
        connect_time = time.time() - start_time
        print(f"✓ Connected successfully in {connect_time:.3f}s")
        
        # Show metrics to see retry attempts
        metrics = client.get_metrics()
        print(f"✓ Connection attempts: {metrics.connection_attempts}")
        print(f"✓ Successful connections: {metrics.successful_connections}")
        print(f"✓ Failed connections: {metrics.failed_connections}")
        
        # Perform operation
        status, data = client.select("INBOX")
        print(f"✓ Selected INBOX with {data[0]} messages")
        
    except Exception as e:
        print(f"✗ Connection failed after all retries: {e}")
        
        # Show final metrics
        metrics = client.get_metrics()
        print(f"Final metrics:")
        print(f"  - Connection attempts: {metrics.connection_attempts}")
        print(f"  - Failed connections: {metrics.failed_connections}")
        print(f"  - Last error: {metrics.last_error}")
        
    finally:
        client.disconnect()


def custom_retry_decorator_example():
    """
    Demonstrates using the retry decorator for custom operations.
    
    This example shows:
    - Custom retry decorator usage
    - Configurable retry parameters
    - Operation-specific retry logic
    - Error handling patterns
    """
    print("\n" + "=" * 60)
    print("CUSTOM RETRY DECORATOR EXAMPLE")
    print("=" * 60)
    
    # Simulate an unreliable operation
    @retry_on_failure(max_retries=3, delay=0.5, exponential_backoff=True)
    def unreliable_operation(success_probability: float = 0.3) -> str:
        """Simulates an operation that fails sometimes."""
        import random
        
        if random.random() < success_probability:
            return "Operation succeeded!"
        else:
            raise Exception("Simulated operation failure")
    
    # Test the retry decorator
    print("Testing retry decorator with unreliable operation...")
    
    for attempt in range(3):
        print(f"\nAttempt {attempt + 1}:")
        try:
            start_time = time.time()
            result = unreliable_operation(success_probability=0.4)
            execution_time = time.time() - start_time
            print(f"✓ {result} (took {execution_time:.3f}s)")
            break
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"✗ Failed: {e} (took {execution_time:.3f}s)")


def network_resilience_example():
    """
    Demonstrates network resilience and recovery mechanisms.
    
    This example shows:
    - Handling network interruptions
    - Automatic reconnection
    - Connection health monitoring
    - Graceful degradation
    """
    print("\n" + "=" * 60)
    print("NETWORK RESILIENCE EXAMPLE")
    print("=" * 60)
    
    # Configuration for resilience testing
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        max_retries=5,
        retry_delay=2.0,
        retry_exponential_backoff=True,
        timeout=20.0,
        health_check_interval=5.0,
        enable_monitoring=True
    )
    
    client = IMAPClient.from_config(config)
    
    try:
        print("Establishing initial connection...")
        client.connect()
        print("✓ Initial connection established")
        
        # Simulate network operations with potential failures
        operations = [
            ("List mailboxes", lambda: client.list()),
            ("Select INBOX", lambda: client.select("INBOX")),
            ("Check server status", lambda: client.noop()),
            ("Get capabilities", lambda: client.capability()),
        ]
        
        for op_name, operation in operations:
            print(f"\nPerforming: {op_name}")
            
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    start_time = time.time()
                    
                    # Check connection health before operation
                    if not client.is_connected():
                        print("  Connection lost, attempting to reconnect...")
                        client.connect()
                    
                    # Perform operation
                    result = operation()
                    execution_time = time.time() - start_time
                    
                    print(f"  ✓ {op_name} completed in {execution_time:.3f}s")
                    break
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    print(f"  ✗ Attempt {attempt + 1} failed: {e} (took {execution_time:.3f}s)")
                    
                    if attempt < max_attempts - 1:
                        print(f"  Retrying in {2 ** attempt}s...")
                        time.sleep(2 ** attempt)
                    else:
                        print(f"  All attempts failed for {op_name}")
        
        # Show final health status
        health = client.health_check()
        print(f"\nFinal Health Status:")
        print(f"  - Connected: {health['is_connected']}")
        print(f"  - Total operations: {health['total_operations']}")
        print(f"  - Success rate: {health['success_rate']:.1f}%")
        
    except Exception as e:
        print(f"✗ Network resilience test failed: {e}")
    finally:
        client.disconnect()


def health_monitoring_example():
    """
    Demonstrates health monitoring and automatic recovery.
    
    This example shows:
    - Background health monitoring
    - Automatic recovery mechanisms
    - Health status reporting
    - Proactive connection management
    """
    print("\n" + "=" * 60)
    print("HEALTH MONITORING EXAMPLE")
    print("=" * 60)
    
    # Configuration with health monitoring
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        health_check_interval=3.0,  # Check every 3 seconds
        enable_monitoring=True,
        max_retries=3,
        retry_delay=1.0
    )
    
    client = IMAPClient.from_config(config)
    
    try:
        print("Starting health monitoring example...")
        print(f"Health check interval: {config.health_check_interval}s")
        
        # Connect and start health monitoring
        client.connect()
        print("✓ Connected with health monitoring enabled")
        
        # Perform operations while monitoring health
        for i in range(5):
            print(f"\nOperation {i + 1}:")
            
            # Check health before operation
            health = client.health_check()
            print(f"  Health check: Connected={health['is_connected']}, "
                  f"Age={health['connection_age']:.1f}s, "
                  f"Success Rate={health['success_rate']:.1f}%")
            
            # Perform operation
            try:
                start_time = time.time()
                status, data = client.select("INBOX")
                op_time = time.time() - start_time
                
                if status == "OK":
                    print(f"  ✓ Operation completed in {op_time:.3f}s")
                else:
                    print(f"  ✗ Operation failed: {status}")
                    
            except Exception as e:
                print(f"  ✗ Operation exception: {e}")
            
            # Wait between operations
            time.sleep(2.0)
        
        # Show final metrics
        metrics = client.get_metrics()
        print(f"\nFinal Metrics:")
        print(f"  - Total operations: {metrics.total_operations}")
        print(f"  - Failed operations: {metrics.failed_operations}")
        print(f"  - Average response time: {metrics.average_response_time:.3f}s")
        print(f"  - Connection uptime: {metrics.connection_uptime}")
        
    except Exception as e:
        print(f"✗ Health monitoring example failed: {e}")
    finally:
        client.disconnect()
        print("✓ Health monitoring stopped")


def connection_recovery_example():
    """
    Demonstrates connection recovery after failures.
    
    This example shows:
    - Detecting connection failures
    - Automatic recovery attempts
    - State preservation during recovery
    - Graceful error handling
    """
    print("\n" + "=" * 60)
    print("CONNECTION RECOVERY EXAMPLE")
    print("=" * 60)
    
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        max_retries=3,
        retry_delay=1.0,
        retry_exponential_backoff=True,
        enable_monitoring=True
    )
    
    client = IMAPClient.from_config(config)
    
    def simulate_connection_loss():
        """Simulate connection loss for testing."""
        print("  Simulating connection loss...")
        if client.connection:
            try:
                client.connection.close()
            except:
                pass
            client.connection = None
    
    try:
        print("Testing connection recovery mechanisms...")
        
        # Initial connection
        client.connect()
        print("✓ Initial connection established")
        
        # Perform initial operations
        status, data = client.select("INBOX")
        print(f"✓ Selected INBOX with {data[0]} messages")
        
        # Simulate connection loss
        simulate_connection_loss()
        print("✗ Connection lost (simulated)")
        
        # Test recovery
        print("\nTesting recovery...")
        recovery_attempts = 0
        max_recovery_attempts = 3
        
        while recovery_attempts < max_recovery_attempts:
            try:
                recovery_attempts += 1
                print(f"Recovery attempt {recovery_attempts}...")
                
                # Check if connection is still valid
                if not client.is_connected():
                    print("  Connection is down, attempting to reconnect...")
                    client.connect()
                
                # Try to perform operation
                status, mailboxes = client.list()
                print(f"  ✓ Recovery successful! Found {len(mailboxes)} mailboxes")
                break
                
            except Exception as e:
                print(f"  ✗ Recovery attempt {recovery_attempts} failed: {e}")
                
                if recovery_attempts < max_recovery_attempts:
                    delay = 2 ** recovery_attempts
                    print(f"  Waiting {delay}s before next attempt...")
                    time.sleep(delay)
                else:
                    print("  All recovery attempts failed")
        
        # Show recovery metrics
        metrics = client.get_metrics()
        print(f"\nRecovery Metrics:")
        print(f"  - Connection attempts: {metrics.connection_attempts}")
        print(f"  - Reconnection attempts: {metrics.reconnection_attempts}")
        print(f"  - Success rate: {((metrics.total_operations - metrics.failed_operations) / metrics.total_operations * 100):.1f}%")
        
    except Exception as e:
        print(f"✗ Connection recovery example failed: {e}")
    finally:
        client.disconnect()


def stress_test_resilience():
    """
    Demonstrates resilience under stress conditions.
    
    This example shows:
    - High-frequency operations
    - Concurrent connection stress
    - Error rate monitoring
    - Performance under load
    """
    print("\n" + "=" * 60)
    print("STRESS TEST RESILIENCE EXAMPLE")
    print("=" * 60)
    
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        max_retries=2,
        retry_delay=0.5,
        timeout=10.0,
        enable_monitoring=True
    )
    
    client = IMAPClient.from_config(config)
    
    try:
        print("Starting stress test...")
        
        client.connect()
        print("✓ Connected for stress test")
        
        # Perform rapid operations
        num_operations = 20
        successful_ops = 0
        failed_ops = 0
        total_time = 0.0
        
        print(f"Performing {num_operations} rapid operations...")
        
        for i in range(num_operations):
            try:
                start_time = time.time()
                
                # Alternate between different operations
                if i % 4 == 0:
                    client.noop()
                elif i % 4 == 1:
                    client.list()
                elif i % 4 == 2:
                    client.select("INBOX")
                else:
                    client.capability()
                
                op_time = time.time() - start_time
                total_time += op_time
                successful_ops += 1
                
                if i % 5 == 0:
                    print(f"  Progress: {i + 1}/{num_operations} operations")
                
            except Exception as e:
                failed_ops += 1
                print(f"  ✗ Operation {i + 1} failed: {e}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Results
        print(f"\nStress Test Results:")
        print(f"  - Total operations: {num_operations}")
        print(f"  - Successful: {successful_ops}")
        print(f"  - Failed: {failed_ops}")
        print(f"  - Success rate: {(successful_ops / num_operations * 100):.1f}%")
        print(f"  - Average time per operation: {(total_time / successful_ops):.3f}s")
        
        # Show client metrics
        metrics = client.get_metrics()
        print(f"\nClient Metrics:")
        print(f"  - Total client operations: {metrics.total_operations}")
        print(f"  - Failed client operations: {metrics.failed_operations}")
        print(f"  - Average response time: {metrics.average_response_time:.3f}s")
        
    except Exception as e:
        print(f"✗ Stress test failed: {e}")
    finally:
        client.disconnect()


def timeout_handling_example():
    """
    Demonstrates timeout handling and configuration.
    
    This example shows:
    - Configurable timeout settings
    - Timeout detection and handling
    - Recovery from timeout errors
    - Adaptive timeout strategies
    """
    print("\n" + "=" * 60)
    print("TIMEOUT HANDLING EXAMPLE")
    print("=" * 60)
    
    # Test different timeout configurations
    timeout_configs = [
        {"name": "Short timeout", "timeout": 5.0},
        {"name": "Medium timeout", "timeout": 15.0},
        {"name": "Long timeout", "timeout": 30.0},
    ]
    
    for config_info in timeout_configs:
        print(f"\nTesting: {config_info['name']} ({config_info['timeout']}s)")
        
        config = ConnectionConfig(
            host="imap.gmail.com",
            username="your_email@gmail.com",
            password="your_password",
            timeout=config_info["timeout"],
            max_retries=2,
            retry_delay=1.0
        )
        
        client = IMAPClient.from_config(config)
        
        try:
            start_time = time.time()
            client.connect()
            connect_time = time.time() - start_time
            
            print(f"  ✓ Connected in {connect_time:.3f}s")
            
            # Perform operation with timeout
            op_start = time.time()
            status, data = client.select("INBOX")
            op_time = time.time() - op_start
            
            print(f"  ✓ Operation completed in {op_time:.3f}s")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"  ✗ Failed after {elapsed:.3f}s: {e}")
        finally:
            client.disconnect()


def main():
    """
    Main function to run all retry and resilience examples.
    
    This function demonstrates comprehensive retry logic and resilience features
    including basic retry, custom decorators, network resilience, health monitoring,
    connection recovery, stress testing, and timeout handling.
    """
    print("Enhanced IMAPClient Retry and Resilience Examples")
    print("=" * 60)
    print("This script demonstrates the retry logic and resilience features of IMAPClient.")
    print("Note: Update the credentials in each example before running.")
    print("Some examples may fail intentionally to demonstrate error handling.")
    print()
    
    # Run all examples
    examples = [
        basic_retry_example,
        custom_retry_decorator_example,
        network_resilience_example,
        health_monitoring_example,
        connection_recovery_example,
        stress_test_resilience,
        timeout_handling_example,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Example {example.__name__} failed: {e}")
        
        # Small delay between examples
        time.sleep(1.0)
    
    print("\n" + "=" * 60)
    print("All retry and resilience examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main() 