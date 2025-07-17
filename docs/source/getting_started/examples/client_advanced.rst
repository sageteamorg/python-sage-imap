.. _client_advanced:

Advanced Client Features
========================

This example demonstrates advanced client features of Python Sage IMAP including connection pooling, monitoring, advanced configuration, and performance optimization.

**⚠️ IMPORTANT: This example shows production-ready advanced patterns!**

Overview
--------

You'll learn how to:

- Use connection pooling for performance
- Configure advanced client options
- Monitor connection health and performance
- Implement retry logic and resilience
- Use multiple connection strategies
- Handle connection timeouts and errors
- Implement connection lifecycle management
- Use advanced authentication methods

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of connection management

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Advanced Client Features Example
   
   This example demonstrates advanced client features including connection pooling,
   monitoring, and performance optimization.
   """
   
   import logging
   import time
   import threading
   from datetime import datetime, timedelta
   from typing import Dict, List, Optional, Any
   from concurrent.futures import ThreadPoolExecutor, as_completed
   
   from sage_imap.services.client import IMAPClient, ConnectionConfig
   from sage_imap.services import IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.exceptions import IMAPConnectionError, IMAPOperationError
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class AdvancedClientExample:
       """
       Advanced client features demonstration.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the advanced client example.
           """
           self.base_config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True
           }
           
           # Performance tracking
           self.performance_metrics = {
               'connection_attempts': 0,
               'successful_connections': 0,
               'failed_connections': 0,
               'total_operations': 0,
               'failed_operations': 0,
               'connection_times': [],
               'operation_times': []
           }
           
       def demonstrate_advanced_features(self):
           """
           Demonstrate all advanced client features.
           """
           logger.info("=== Advanced Client Features Example ===")
           
           try:
               # Connection pooling
               self.demonstrate_connection_pooling()
               
               # Advanced configuration
               self.demonstrate_advanced_configuration()
               
               # Health monitoring
               self.demonstrate_health_monitoring()
               
               # Retry mechanisms
               self.demonstrate_retry_mechanisms()
               
               # Performance optimization
               self.demonstrate_performance_optimization()
               
               # Connection lifecycle management
               self.demonstrate_connection_lifecycle()
               
               # Multiple connection strategies
               self.demonstrate_multiple_connections()
               
               # Generate performance report
               self.generate_performance_report()
               
               logger.info("✓ Advanced client features completed successfully")
               
           except Exception as e:
               logger.error(f"❌ Advanced client features failed: {e}")
               raise
   
       def demonstrate_connection_pooling(self):
           """
           Demonstrate connection pooling features.
           """
           logger.info("--- Connection Pooling ---")
           
           try:
               # Basic connection pooling
               config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   use_pool=True,
                   pool_size=5,
                   max_connections=10
               )
               
               logger.info("  📡 Testing connection pooling...")
               
               # Test multiple connections
               connections = []
               for i in range(3):
                   try:
                       client = IMAPClient(config=config)
                       client.connect()
                       connections.append(client)
                       logger.info(f"    ✓ Connection {i+1} established")
                   except Exception as e:
                       logger.error(f"    ❌ Connection {i+1} failed: {e}")
               
               # Use connections
               for i, client in enumerate(connections):
                   try:
                       uid_service = IMAPMailboxUIDService(client)
                       uid_service.select("INBOX")
                       status = uid_service.get_mailbox_status()
                       if status.success:
                           logger.info(f"    ✓ Connection {i+1} - Mailbox status retrieved")
                   except Exception as e:
                       logger.error(f"    ❌ Connection {i+1} operation failed: {e}")
               
               # Close connections
               for client in connections:
                   try:
                       client.disconnect()
                   except Exception as e:
                       logger.warning(f"    ⚠ Error closing connection: {e}")
               
               logger.info("  ✓ Connection pooling demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed connection pooling demonstration: {e}")
   
       def demonstrate_advanced_configuration(self):
           """
           Demonstrate advanced configuration options.
           """
           logger.info("--- Advanced Configuration ---")
           
           try:
               # Advanced configuration with all options
               advanced_config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   timeout=30.0,
                   max_retries=3,
                   retry_delay=1.0,
                   retry_exponential_backoff=True,
                   max_retry_delay=10.0,
                   keepalive_interval=300.0,
                   health_check_interval=60.0,
                   enable_monitoring=True,
                   compression=True,
                   debug=False
               )
               
               logger.info("  ⚙️ Advanced configuration options:")
               logger.info(f"    • Timeout: {advanced_config.timeout}s")
               logger.info(f"    • Max retries: {advanced_config.max_retries}")
               logger.info(f"    • Retry delay: {advanced_config.retry_delay}s")
               logger.info(f"    • Exponential backoff: {advanced_config.retry_exponential_backoff}")
               logger.info(f"    • Keepalive interval: {advanced_config.keepalive_interval}s")
               logger.info(f"    • Health check interval: {advanced_config.health_check_interval}s")
               logger.info(f"    • Monitoring enabled: {advanced_config.enable_monitoring}")
               logger.info(f"    • Compression: {advanced_config.compression}")
               
               # Test advanced configuration
               with IMAPClient(config=advanced_config) as client:
                   logger.info("  ✓ Advanced configuration client connected")
                   
                   # Test operations with advanced config
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Test with monitoring
                   if advanced_config.enable_monitoring:
                       metrics = client.get_metrics()
                       logger.info(f"    📊 Connection metrics available: {bool(metrics)}")
               
               logger.info("  ✓ Advanced configuration demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed advanced configuration demonstration: {e}")
   
       def demonstrate_health_monitoring(self):
           """
           Demonstrate health monitoring capabilities.
           """
           logger.info("--- Health Monitoring ---")
           
           try:
               # Configuration with monitoring enabled
               config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   enable_monitoring=True,
                   health_check_interval=30.0
               )
               
               logger.info("  🏥 Health monitoring demonstration:")
               
               with IMAPClient(config=config) as client:
                   logger.info("    ✓ Client connected with monitoring")
                   
                   # Perform operations to generate metrics
                   uid_service = IMAPMailboxUIDService(client)
                   
                   operations = [
                       ("Select INBOX", lambda: uid_service.select("INBOX")),
                       ("Get status", lambda: uid_service.get_mailbox_status()),
                       ("Search messages", lambda: uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL))
                   ]
                   
                   for operation_name, operation in operations:
                       try:
                           start_time = time.time()
                           result = operation()
                           operation_time = time.time() - start_time
                           
                           self.performance_metrics['total_operations'] += 1
                           self.performance_metrics['operation_times'].append(operation_time)
                           
                           if hasattr(result, 'success') and result.success:
                               logger.info(f"    ✓ {operation_name}: {operation_time:.3f}s")
                           else:
                               logger.info(f"    ✓ {operation_name}: {operation_time:.3f}s")
                       except Exception as e:
                           self.performance_metrics['failed_operations'] += 1
                           logger.error(f"    ❌ {operation_name} failed: {e}")
                   
                   # Get health metrics
                   try:
                       metrics = client.get_metrics()
                       if metrics:
                           logger.info("    📊 Health metrics:")
                           logger.info(f"      • Connection attempts: {metrics.get('connection_attempts', 0)}")
                           logger.info(f"      • Successful connections: {metrics.get('successful_connections', 0)}")
                           logger.info(f"      • Failed connections: {metrics.get('failed_connections', 0)}")
                           logger.info(f"      • Total operations: {metrics.get('total_operations', 0)}")
                           logger.info(f"      • Average response time: {metrics.get('average_response_time', 0):.3f}s")
                   except Exception as e:
                       logger.warning(f"    ⚠ Could not retrieve metrics: {e}")
               
               logger.info("  ✓ Health monitoring demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed health monitoring demonstration: {e}")
   
       def demonstrate_retry_mechanisms(self):
           """
           Demonstrate retry mechanisms and resilience.
           """
           logger.info("--- Retry Mechanisms ---")
           
           try:
               # Configuration with retry settings
               retry_config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   max_retries=3,
                   retry_delay=1.0,
                   retry_exponential_backoff=True,
                   max_retry_delay=10.0,
                   timeout=10.0
               )
               
               logger.info("  🔄 Retry mechanism demonstration:")
               logger.info(f"    • Max retries: {retry_config.max_retries}")
               logger.info(f"    • Base delay: {retry_config.retry_delay}s")
               logger.info(f"    • Exponential backoff: {retry_config.retry_exponential_backoff}")
               logger.info(f"    • Max delay: {retry_config.max_retry_delay}s")
               
               # Test retry mechanism
               retry_attempts = 0
               max_attempts = 3
               
               while retry_attempts < max_attempts:
                   try:
                       retry_attempts += 1
                       logger.info(f"    Attempt {retry_attempts}/{max_attempts}")
                       
                       with IMAPClient(config=retry_config) as client:
                           uid_service = IMAPMailboxUIDService(client)
                           uid_service.select("INBOX")
                           
                           # Simulate operations
                           result = uid_service.get_mailbox_status()
                           if result.success:
                               logger.info(f"    ✓ Operation successful on attempt {retry_attempts}")
                               break
                           else:
                               logger.warning(f"    ⚠ Operation failed on attempt {retry_attempts}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Attempt {retry_attempts} failed: {e}")
                       
                       if retry_attempts < max_attempts:
                           delay = retry_config.retry_delay * (2 ** (retry_attempts - 1))
                           delay = min(delay, retry_config.max_retry_delay)
                           logger.info(f"    ⏳ Waiting {delay}s before retry...")
                           time.sleep(delay)
                       else:
                           logger.error(f"    ❌ All {max_attempts} attempts failed")
               
               logger.info("  ✓ Retry mechanism demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed retry mechanism demonstration: {e}")
   
       def demonstrate_performance_optimization(self):
           """
           Demonstrate performance optimization techniques.
           """
           logger.info("--- Performance Optimization ---")
           
           try:
               # Optimized configuration
               optimized_config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   use_pool=True,
                   pool_size=3,
                   compression=True,
                   keepalive_interval=300.0,
                   timeout=30.0
               )
               
               logger.info("  🚀 Performance optimization demonstration:")
               
               # Test performance with different configurations
               configs = [
                   ("Basic", ConnectionConfig(
                       host=self.base_config['host'],
                       username=self.base_config['username'],
                       password=self.base_config['password'],
                       port=self.base_config['port'],
                       use_ssl=True
                   )),
                   ("Optimized", optimized_config)
               ]
               
               for config_name, config in configs:
                   try:
                       logger.info(f"    Testing {config_name} configuration:")
                       
                       # Time connection establishment
                       start_time = time.time()
                       with IMAPClient(config=config) as client:
                           connection_time = time.time() - start_time
                           
                           # Time operations
                           uid_service = IMAPMailboxUIDService(client)
                           
                           operation_start = time.time()
                           uid_service.select("INBOX")
                           status_result = uid_service.get_mailbox_status()
                           operation_time = time.time() - operation_start
                           
                           logger.info(f"      • Connection time: {connection_time:.3f}s")
                           logger.info(f"      • Operation time: {operation_time:.3f}s")
                           
                           if status_result.success:
                               status = status_result.metadata
                               logger.info(f"      • Messages: {status.get('EXISTS', 0)}")
                   
                   except Exception as e:
                       logger.error(f"      ❌ {config_name} configuration failed: {e}")
               
               logger.info("  ✓ Performance optimization demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed performance optimization demonstration: {e}")
   
       def demonstrate_connection_lifecycle(self):
           """
           Demonstrate connection lifecycle management.
           """
           logger.info("--- Connection Lifecycle Management ---")
           
           try:
               config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   keepalive_interval=60.0,
                   health_check_interval=30.0
               )
               
               logger.info("  🔄 Connection lifecycle demonstration:")
               
               # Manual connection management
               client = IMAPClient(config=config)
               
               try:
                   # Connect
                   logger.info("    📡 Connecting...")
                   start_time = time.time()
                   client.connect()
                   connect_time = time.time() - start_time
                   
                   self.performance_metrics['connection_attempts'] += 1
                   self.performance_metrics['successful_connections'] += 1
                   self.performance_metrics['connection_times'].append(connect_time)
                   
                   logger.info(f"    ✓ Connected in {connect_time:.3f}s")
                   
                   # Check connection health
                   if client.is_connected():
                       logger.info("    ✓ Connection is healthy")
                   
                   # Perform operations
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Simulate long-running operations
                   logger.info("    🔄 Performing operations...")
                   for i in range(3):
                       try:
                           result = uid_service.get_mailbox_status()
                           if result.success:
                               logger.info(f"      ✓ Operation {i+1} successful")
                           else:
                               logger.warning(f"      ⚠ Operation {i+1} failed")
                           
                           # Brief pause between operations
                           time.sleep(0.5)
                       except Exception as e:
                           logger.error(f"      ❌ Operation {i+1} error: {e}")
                   
                   # Check connection health after operations
                   if client.is_connected():
                       logger.info("    ✓ Connection still healthy after operations")
                   else:
                       logger.warning("    ⚠ Connection became unhealthy")
               
               finally:
                   # Disconnect
                   logger.info("    🔌 Disconnecting...")
                   try:
                       client.disconnect()
                       logger.info("    ✓ Disconnected successfully")
                   except Exception as e:
                       logger.error(f"    ❌ Disconnect error: {e}")
               
               logger.info("  ✓ Connection lifecycle demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed connection lifecycle demonstration: {e}")
   
       def demonstrate_multiple_connections(self):
           """
           Demonstrate managing multiple connections.
           """
           logger.info("--- Multiple Connection Management ---")
           
           try:
               config = ConnectionConfig(
                   host=self.base_config['host'],
                   username=self.base_config['username'],
                   password=self.base_config['password'],
                   port=self.base_config['port'],
                   use_ssl=True,
                   use_pool=True,
                   pool_size=5
               )
               
               logger.info("  🔗 Multiple connection demonstration:")
               
               # Thread-safe connection management
               connection_results = []
               
               def worker_function(worker_id):
                   """Worker function for testing multiple connections."""
                   try:
                       with IMAPClient(config=config) as client:
                           uid_service = IMAPMailboxUIDService(client)
                           uid_service.select("INBOX")
                           
                           # Perform operations
                           result = uid_service.get_mailbox_status()
                           
                           return {
                               'worker_id': worker_id,
                               'success': result.success if hasattr(result, 'success') else True,
                               'messages': result.metadata.get('EXISTS', 0) if hasattr(result, 'metadata') and result.metadata else 0
                           }
                   except Exception as e:
                       return {
                           'worker_id': worker_id,
                           'success': False,
                           'error': str(e)
                       }
               
               # Use ThreadPoolExecutor for concurrent connections
               with ThreadPoolExecutor(max_workers=3) as executor:
                   futures = [executor.submit(worker_function, i) for i in range(3)]
                   
                   for future in as_completed(futures):
                       try:
                           result = future.result()
                           connection_results.append(result)
                           
                           if result['success']:
                               logger.info(f"    ✓ Worker {result['worker_id']}: {result.get('messages', 0)} messages")
                           else:
                               logger.error(f"    ❌ Worker {result['worker_id']}: {result.get('error', 'Unknown error')}")
                       except Exception as e:
                           logger.error(f"    ❌ Worker future error: {e}")
               
               # Summary
               successful_workers = sum(1 for r in connection_results if r['success'])
               logger.info(f"  📊 Multiple connections: {successful_workers}/{len(connection_results)} successful")
               
               logger.info("  ✓ Multiple connection demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed multiple connection demonstration: {e}")
   
       def generate_performance_report(self):
           """
           Generate a performance report for all operations.
           """
           logger.info("--- Performance Report ---")
           
           try:
               metrics = self.performance_metrics
               
               logger.info("  📊 Advanced Client Performance Report:")
               logger.info("  " + "=" * 50)
               
               # Connection metrics
               logger.info(f"  Connection Attempts: {metrics['connection_attempts']}")
               logger.info(f"  Successful Connections: {metrics['successful_connections']}")
               logger.info(f"  Failed Connections: {metrics['failed_connections']}")
               
               if metrics['connection_times']:
                   avg_connection_time = sum(metrics['connection_times']) / len(metrics['connection_times'])
                   min_connection_time = min(metrics['connection_times'])
                   max_connection_time = max(metrics['connection_times'])
                   
                   logger.info(f"  Average Connection Time: {avg_connection_time:.3f}s")
                   logger.info(f"  Min Connection Time: {min_connection_time:.3f}s")
                   logger.info(f"  Max Connection Time: {max_connection_time:.3f}s")
               
               # Operation metrics
               logger.info(f"  Total Operations: {metrics['total_operations']}")
               logger.info(f"  Failed Operations: {metrics['failed_operations']}")
               
               if metrics['operation_times']:
                   avg_operation_time = sum(metrics['operation_times']) / len(metrics['operation_times'])
                   min_operation_time = min(metrics['operation_times'])
                   max_operation_time = max(metrics['operation_times'])
                   
                   logger.info(f"  Average Operation Time: {avg_operation_time:.3f}s")
                   logger.info(f"  Min Operation Time: {min_operation_time:.3f}s")
                   logger.info(f"  Max Operation Time: {max_operation_time:.3f}s")
               
               # Success rates
               if metrics['connection_attempts'] > 0:
                   connection_success_rate = (metrics['successful_connections'] / metrics['connection_attempts']) * 100
                   logger.info(f"  Connection Success Rate: {connection_success_rate:.1f}%")
               
               if metrics['total_operations'] > 0:
                   operation_success_rate = ((metrics['total_operations'] - metrics['failed_operations']) / metrics['total_operations']) * 100
                   logger.info(f"  Operation Success Rate: {operation_success_rate:.1f}%")
               
               logger.info("  " + "=" * 50)
               
           except Exception as e:
               logger.error(f"Failed to generate performance report: {e}")


   def main():
       """
       Main function to run the advanced client example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = AdvancedClientExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_advanced_features()
           logger.info("🎉 Advanced client features example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Advanced Configuration Options
------------------------------

ConnectionConfig Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   config = ConnectionConfig(
       # Basic connection
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_password",
       port=993,
       use_ssl=True,
       
       # Timeouts and retries
       timeout=30.0,
       max_retries=3,
       retry_delay=1.0,
       retry_exponential_backoff=True,
       max_retry_delay=10.0,
       
       # Connection pooling
       use_pool=True,
       pool_size=5,
       max_connections=10,
       
       # Health and monitoring
       keepalive_interval=300.0,
       health_check_interval=60.0,
       enable_monitoring=True,
       
       # Performance
       compression=True,
       debug=False
   )

Connection Pooling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable connection pooling
   config = ConnectionConfig(
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_password",
       use_pool=True,
       pool_size=5,
       max_connections=10
   )
   
   # Reuse connections automatically
   with IMAPClient(config=config) as client:
       # Operations reuse pooled connections
       pass

Health Monitoring
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable health monitoring
   config = ConnectionConfig(
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_password",
       enable_monitoring=True,
       health_check_interval=60.0
   )
   
   with IMAPClient(config=config) as client:
       # Get health metrics
       metrics = client.get_metrics()
       
       print(f"Connection attempts: {metrics.connection_attempts}")
       print(f"Success rate: {metrics.success_rate:.1f}%")
       print(f"Average response time: {metrics.average_response_time:.3f}s")

Retry Mechanisms
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Configure retry behavior
   config = ConnectionConfig(
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_password",
       max_retries=3,
       retry_delay=1.0,
       retry_exponential_backoff=True,
       max_retry_delay=10.0
   )
   
   # Automatic retry on failures
   with IMAPClient(config=config) as client:
       # Operations automatically retry on failure
       pass

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimized configuration
   config = ConnectionConfig(
       host="imap.gmail.com",
       username="your_email@gmail.com",
       password="your_app_password",
       use_pool=True,
       pool_size=3,
       compression=True,
       keepalive_interval=300.0,
       timeout=30.0
   )

Multiple Connection Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Thread-safe multiple connections
   from concurrent.futures import ThreadPoolExecutor
   
   def worker_function(worker_id):
       with IMAPClient(config=config) as client:
           uid_service = IMAPMailboxUIDService(client)
           uid_service.select("INBOX")
           return uid_service.get_mailbox_status()
   
   with ThreadPoolExecutor(max_workers=3) as executor:
       futures = [executor.submit(worker_function, i) for i in range(3)]
       results = [future.result() for future in futures]

Connection Lifecycle
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Manual connection management
   client = IMAPClient(config=config)
   
   try:
       # Connect
       client.connect()
       
       # Check health
       if client.is_connected():
           print("Connection is healthy")
       
       # Perform operations
       uid_service = IMAPMailboxUIDService(client)
       uid_service.select("INBOX")
       
   finally:
       # Always disconnect
       client.disconnect()

Best Practices
--------------

✅ **DO:**

- Use connection pooling for better performance

- Enable health monitoring in production

- Configure appropriate timeouts

- Implement retry logic for resilience

- Use multiple connections for concurrent operations

- Monitor connection metrics

- Handle connection lifecycle properly

❌ **DON'T:**

- Create excessive connections

- Ignore connection health

- Use infinite retries

- Skip connection cleanup

- Ignore performance metrics

- Use blocking operations in threads

- Forget timeout configurations

Common Configuration Patterns
-----------------------------

Development Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   dev_config = ConnectionConfig(
       host="imap.gmail.com",
       username="dev@example.com",
       password="dev_password",
       timeout=10.0,
       max_retries=1,
       debug=True
   )

Production Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   prod_config = ConnectionConfig(
       host="imap.company.com",
       username="service@company.com",
       password="secure_password",
       use_pool=True,
       pool_size=5,
       max_connections=20,
       timeout=30.0,
       max_retries=3,
       retry_exponential_backoff=True,
       keepalive_interval=300.0,
       health_check_interval=60.0,
       enable_monitoring=True,
       compression=True
   )

High-Performance Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   high_perf_config = ConnectionConfig(
       host="imap.company.com",
       username="service@company.com",
       password="secure_password",
       use_pool=True,
       pool_size=10,
       max_connections=50,
       timeout=60.0,
       compression=True,
       keepalive_interval=600.0,
       enable_monitoring=True
   )

Next Steps
----------

For more advanced patterns, see:

- :doc:`large_volume_handling` - High-performance processing
- :doc:`production_patterns` - Production-ready patterns
- :doc:`monitoring_analytics` - Monitoring and analytics
- :doc:`error_handling` - Error handling strategies 