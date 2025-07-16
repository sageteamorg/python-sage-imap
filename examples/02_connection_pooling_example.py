#!/usr/bin/env python3
"""
Connection Pooling Example

This example demonstrates the advanced connection pooling features of the enhanced
IMAPClient including pool management, connection reuse, and performance optimization.

Author: Python Sage IMAP Library
License: MIT
"""

import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from sage_imap.services.client import (
    IMAPClient, 
    ConnectionConfig, 
    clear_connection_pool,
    get_pool_stats
)
from sage_imap.exceptions import IMAPConnectionError, IMAPAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def basic_pooling_example():
    """
    Demonstrates basic connection pooling functionality.
    
    This example shows:
    - Enabling connection pooling
    - Connection reuse from pool
    - Pool statistics monitoring
    - Automatic pool management
    """
    print("=" * 60)
    print("BASIC CONNECTION POOLING EXAMPLE")
    print("=" * 60)
    
    # Configuration
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    # Clear any existing pool connections
    clear_connection_pool()
    
    # Create client with pooling enabled
    client = IMAPClient(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
        use_pool=True  # Enable connection pooling
    )
    
    try:
        print("Initial pool stats:")
        stats = get_pool_stats()
        print(f"  - Max connections: {stats['max_connections']}")
        print(f"  - Active pools: {stats['active_pools']}")
        print(f"  - Total pooled connections: {stats['total_pooled_connections']}")
        
        # First connection - will create new connection
        print("\nFirst connection (creates new):")
        start_time = time.time()
        client.connect()
        connect_time = time.time() - start_time
        print(f"✓ Connected in {connect_time:.3f}s")
        
        # Perform some operations
        status, data = client.select("INBOX")
        print(f"✓ Selected INBOX with {data[0]} messages")
        
        # Disconnect (returns to pool)
        client.disconnect()
        print("✓ Connection returned to pool")
        
        # Check pool stats after first connection
        stats = get_pool_stats()
        print(f"\nPool stats after first connection:")
        print(f"  - Active pools: {stats['active_pools']}")
        print(f"  - Total pooled connections: {stats['total_pooled_connections']}")
        
        # Second connection - should reuse from pool
        print("\nSecond connection (reuses from pool):")
        start_time = time.time()
        client.connect()
        connect_time = time.time() - start_time
        print(f"✓ Connected in {connect_time:.3f}s (faster due to pooling)")
        
        # Perform operations
        status, mailboxes = client.list()
        print(f"✓ Found {len(mailboxes)} mailboxes")
        
        client.disconnect()
        print("✓ Connection returned to pool")
        
    except Exception as e:
        print(f"✗ Pooling example failed: {e}")
    finally:
        # Clean up
        client.disconnect()


def concurrent_pooling_example():
    """
    Demonstrates concurrent connection pooling with multiple threads.
    
    This example shows:
    - Multiple concurrent connections
    - Pool sharing between threads
    - Connection distribution
    - Performance benefits of pooling
    """
    print("\n" + "=" * 60)
    print("CONCURRENT CONNECTION POOLING EXAMPLE")
    print("=" * 60)
    
    # Configuration
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    # Clear pool
    clear_connection_pool()
    
    def worker_task(worker_id: int) -> Dict[str, Any]:
        """Worker function that uses pooled connections."""
        client = IMAPClient(
            host=HOST,
            username=USERNAME,
            password=PASSWORD,
            use_pool=True
        )
        
        results = {
            "worker_id": worker_id,
            "operations": 0,
            "total_time": 0.0,
            "errors": []
        }
        
        try:
            # Perform multiple operations
            for i in range(3):
                start_time = time.time()
                
                # Connect (may reuse from pool)
                client.connect()
                
                # Perform operation
                if i == 0:
                    status, data = client.select("INBOX")
                    operation = f"select INBOX ({data[0]} messages)"
                elif i == 1:
                    status, mailboxes = client.list()
                    operation = f"list mailboxes ({len(mailboxes)} found)"
                else:
                    status, response = client.noop()
                    operation = "noop"
                
                client.disconnect()
                
                op_time = time.time() - start_time
                results["operations"] += 1
                results["total_time"] += op_time
                
                print(f"Worker {worker_id}: {operation} in {op_time:.3f}s")
                
        except Exception as e:
            results["errors"].append(str(e))
            print(f"Worker {worker_id} error: {e}")
        
        return results
    
    # Run concurrent workers
    num_workers = 5
    print(f"Starting {num_workers} concurrent workers...")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit tasks
        futures = [executor.submit(worker_task, i) for i in range(num_workers)]
        
        # Collect results
        all_results = []
        for future in as_completed(futures):
            result = future.result()
            all_results.append(result)
    
    total_time = time.time() - start_time
    
    # Analyze results
    print(f"\nConcurrent execution completed in {total_time:.3f}s")
    
    total_operations = sum(r["operations"] for r in all_results)
    total_errors = sum(len(r["errors"]) for r in all_results)
    avg_time_per_op = sum(r["total_time"] for r in all_results) / total_operations if total_operations > 0 else 0
    
    print(f"Results:")
    print(f"  - Total operations: {total_operations}")
    print(f"  - Total errors: {total_errors}")
    print(f"  - Average time per operation: {avg_time_per_op:.3f}s")
    print(f"  - Success rate: {((total_operations - total_errors) / total_operations * 100):.1f}%")
    
    # Show final pool stats
    stats = get_pool_stats()
    print(f"\nFinal pool stats:")
    print(f"  - Active pools: {stats['active_pools']}")
    print(f"  - Total pooled connections: {stats['total_pooled_connections']}")


def pool_configuration_example():
    """
    Demonstrates advanced pool configuration and management.
    
    This example shows:
    - Custom pool configurations
    - Pool size management
    - Connection lifecycle
    - Pool monitoring
    """
    print("\n" + "=" * 60)
    print("POOL CONFIGURATION EXAMPLE")
    print("=" * 60)
    
    # Configuration
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        max_retries=3,
        retry_delay=1.0,
        timeout=30.0,
        enable_monitoring=True
    )
    
    # Clear pool
    clear_connection_pool()
    
    # Create multiple clients with same configuration
    clients = [
        IMAPClient.from_config(config, use_pool=True) 
        for _ in range(3)
    ]
    
    try:
        print("Testing pool with multiple clients...")
        
        # Connect all clients
        for i, client in enumerate(clients):
            print(f"\nClient {i+1} connecting...")
            client.connect()
            
            # Show pool stats
            stats = get_pool_stats()
            print(f"  Pool stats: {stats['total_pooled_connections']} connections")
            
            # Perform operation
            status, data = client.select("INBOX")
            print(f"  ✓ Selected INBOX with {data[0]} messages")
        
        # Disconnect all clients (return to pool)
        print("\nDisconnecting all clients...")
        for i, client in enumerate(clients):
            client.disconnect()
            print(f"  Client {i+1} disconnected")
        
        # Show final pool stats
        stats = get_pool_stats()
        print(f"\nFinal pool stats:")
        print(f"  - Max connections: {stats['max_connections']}")
        print(f"  - Active pools: {stats['active_pools']}")
        print(f"  - Total pooled connections: {stats['total_pooled_connections']}")
        
        # Test connection reuse
        print("\nTesting connection reuse...")
        for i, client in enumerate(clients):
            start_time = time.time()
            client.connect()
            connect_time = time.time() - start_time
            print(f"  Client {i+1} reconnected in {connect_time:.3f}s (from pool)")
            client.disconnect()
        
    except Exception as e:
        print(f"✗ Pool configuration example failed: {e}")
    finally:
        # Clean up all clients
        for client in clients:
            client.disconnect()


def pool_performance_comparison():
    """
    Demonstrates performance comparison between pooled and non-pooled connections.
    
    This example shows:
    - Performance metrics with pooling
    - Performance metrics without pooling
    - Comparison analysis
    - Best practices
    """
    print("\n" + "=" * 60)
    print("POOL PERFORMANCE COMPARISON")
    print("=" * 60)
    
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    def performance_test(use_pool: bool, num_operations: int = 10) -> Dict[str, Any]:
        """Run performance test with or without pooling."""
        client = IMAPClient(
            host=HOST,
            username=USERNAME,
            password=PASSWORD,
            use_pool=use_pool
        )
        
        results = {
            "use_pool": use_pool,
            "num_operations": num_operations,
            "total_time": 0.0,
            "connection_times": [],
            "operation_times": [],
            "errors": 0
        }
        
        total_start = time.time()
        
        for i in range(num_operations):
            try:
                # Time connection
                conn_start = time.time()
                client.connect()
                conn_time = time.time() - conn_start
                results["connection_times"].append(conn_time)
                
                # Time operation
                op_start = time.time()
                status, data = client.select("INBOX")
                op_time = time.time() - op_start
                results["operation_times"].append(op_time)
                
                client.disconnect()
                
            except Exception as e:
                results["errors"] += 1
                logger.error(f"Operation {i} failed: {e}")
        
        results["total_time"] = time.time() - total_start
        
        return results
    
    # Clear pool for fair comparison
    clear_connection_pool()
    
    # Test without pooling
    print("Testing without connection pooling...")
    no_pool_results = performance_test(use_pool=False, num_operations=5)
    
    # Test with pooling
    print("Testing with connection pooling...")
    pool_results = performance_test(use_pool=True, num_operations=5)
    
    # Compare results
    print("\nPerformance Comparison:")
    print("=" * 40)
    
    print(f"Without Pooling:")
    print(f"  - Total time: {no_pool_results['total_time']:.3f}s")
    print(f"  - Avg connection time: {sum(no_pool_results['connection_times'])/len(no_pool_results['connection_times']):.3f}s")
    print(f"  - Avg operation time: {sum(no_pool_results['operation_times'])/len(no_pool_results['operation_times']):.3f}s")
    print(f"  - Errors: {no_pool_results['errors']}")
    
    print(f"\nWith Pooling:")
    print(f"  - Total time: {pool_results['total_time']:.3f}s")
    print(f"  - Avg connection time: {sum(pool_results['connection_times'])/len(pool_results['connection_times']):.3f}s")
    print(f"  - Avg operation time: {sum(pool_results['operation_times'])/len(pool_results['operation_times']):.3f}s")
    print(f"  - Errors: {pool_results['errors']}")
    
    # Calculate improvement
    time_improvement = ((no_pool_results['total_time'] - pool_results['total_time']) / 
                       no_pool_results['total_time'] * 100)
    
    print(f"\nImprovement with pooling: {time_improvement:.1f}% faster")


def pool_monitoring_example():
    """
    Demonstrates comprehensive pool monitoring and management.
    
    This example shows:
    - Pool statistics monitoring
    - Connection lifecycle tracking
    - Pool health monitoring
    - Troubleshooting techniques
    """
    print("\n" + "=" * 60)
    print("POOL MONITORING EXAMPLE")
    print("=" * 60)
    
    HOST = "mail.sageteam.org"
    USERNAME = "cmo@window.qa"
    PASSWORD = "FAntRo,?,54"
    
    # Clear pool
    clear_connection_pool()
    
    def monitor_pool_stats():
        """Helper function to display pool statistics."""
        stats = get_pool_stats()
        print(f"  Pool Stats: {stats['active_pools']} pools, {stats['total_pooled_connections']} connections")
    
    print("Initial pool state:")
    monitor_pool_stats()
    
    # Create multiple clients
    clients = []
    for i in range(3):
        client = IMAPClient(
            host=HOST,
            username=USERNAME,
            password=PASSWORD,
            use_pool=True
        )
        clients.append(client)
    
    try:
        # Connect clients sequentially
        print("\nConnecting clients sequentially:")
        for i, client in enumerate(clients):
            print(f"Connecting client {i+1}...")
            client.connect()
            monitor_pool_stats()
        
        # Disconnect clients (return to pool)
        print("\nDisconnecting clients (returning to pool):")
        for i, client in enumerate(clients):
            print(f"Disconnecting client {i+1}...")
            client.disconnect()
            monitor_pool_stats()
        
        # Reconnect to show pool reuse
        print("\nReconnecting to demonstrate pool reuse:")
        for i, client in enumerate(clients):
            start_time = time.time()
            client.connect()
            connect_time = time.time() - start_time
            print(f"Client {i+1} reconnected in {connect_time:.3f}s")
            monitor_pool_stats()
        
        # Show detailed pool information
        print("\nDetailed pool information:")
        stats = get_pool_stats()
        print(f"  - Maximum connections per pool: {stats['max_connections']}")
        print(f"  - Number of active pools: {stats['active_pools']}")
        print(f"  - Total pooled connections: {stats['total_pooled_connections']}")
        
    except Exception as e:
        print(f"✗ Pool monitoring example failed: {e}")
    finally:
        # Clean up
        for client in clients:
            client.disconnect()
        
        print("\nFinal cleanup:")
        monitor_pool_stats()


def main():
    """
    Main function to run all connection pooling examples.
    
    This function demonstrates comprehensive connection pooling features
    including basic usage, concurrent operations, configuration, performance,
    and monitoring.
    """
    print("Enhanced IMAPClient Connection Pooling Examples")
    print("=" * 60)
    print("This script demonstrates the connection pooling features of IMAPClient.")
    print("Note: Update the credentials in each example before running.")
    print()
    
    # Run all examples
    examples = [
        basic_pooling_example,
        concurrent_pooling_example,
        pool_configuration_example,
        pool_performance_comparison,
        pool_monitoring_example,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Example {example.__name__} failed: {e}")
        
        # Small delay between examples
        time.sleep(1.0)
    
    # Final cleanup
    clear_connection_pool()
    
    print("\n" + "=" * 60)
    print("All connection pooling examples completed!")
    print("Connection pool cleared.")
    print("=" * 60)


if __name__ == "__main__":
    main() 