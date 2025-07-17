.. _production_patterns:

Production Patterns
===================

This example demonstrates production-ready patterns for deploying Python Sage IMAP in production environments with proper configuration, monitoring, and best practices.

**⚠️ IMPORTANT: This example covers enterprise-grade production patterns!**

Overview
--------

You'll learn how to:

- Configure production-ready IMAP clients
- Implement proper logging and monitoring
- Handle errors and failures gracefully
- Manage configuration and secrets
- Deploy with high availability
- Implement health checks and metrics
- Use connection pooling and caching
- Handle scaling and performance

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Understanding of production deployment
- Knowledge of monitoring and logging

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Production Patterns Example
   
   This example demonstrates production-ready patterns for deploying
   Python Sage IMAP in enterprise environments.
   """
   
   import logging
   import logging.handlers
   import os
   import time
   import json
   import threading
   from datetime import datetime, timedelta
   from typing import Dict, List, Optional, Any
   from pathlib import Path
   import signal
   import sys
   
   from sage_imap.services.client import IMAPClient, ConnectionConfig
   from sage_imap.services import IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.exceptions import IMAPConnectionError, IMAPOperationError
   
   
   class ProductionIMAPService:
       """
       Production-ready IMAP service with enterprise patterns.
       """
       
       def __init__(self, config_path: str = None):
           """
           Initialize production IMAP service.
           """
           self.config_path = config_path or os.getenv('IMAP_CONFIG_PATH', 'config/production.json')
           self.config = self.load_configuration()
           
           # Setup logging
           self.setup_production_logging()
           self.logger = logging.getLogger(__name__)
           
           # Initialize metrics
           self.metrics = ProductionMetrics()
           
           # Health monitoring
           self.health_monitor = HealthMonitor(self)
           
           # Connection pool
           self.connection_pool = ConnectionPool(self.config)
           
           # Graceful shutdown
           self.shutdown_event = threading.Event()
           self.setup_signal_handlers()
           
           self.logger.info("Production IMAP service initialized")
   
       def load_configuration(self) -> Dict[str, Any]:
           """
           Load production configuration from file or environment.
           """
           try:
               # Try to load from file
               if os.path.exists(self.config_path):
                   with open(self.config_path, 'r') as f:
                       config = json.load(f)
               else:
                   # Fallback to environment variables
                   config = self.load_from_environment()
               
               # Validate configuration
               self.validate_configuration(config)
               
               return config
               
           except Exception as e:
               # Fallback configuration
               logging.error(f"Failed to load configuration: {e}")
               return self.get_default_configuration()
   
       def load_from_environment(self) -> Dict[str, Any]:
           """
           Load configuration from environment variables.
           """
           return {
               'imap': {
                   'host': os.getenv('IMAP_HOST', 'imap.gmail.com'),
                   'port': int(os.getenv('IMAP_PORT', '993')),
                   'username': os.getenv('IMAP_USERNAME'),
                   'password': os.getenv('IMAP_PASSWORD'),
                   'use_ssl': os.getenv('IMAP_USE_SSL', 'true').lower() == 'true',
                   'timeout': float(os.getenv('IMAP_TIMEOUT', '30.0')),
                   'max_retries': int(os.getenv('IMAP_MAX_RETRIES', '3')),
                   'retry_delay': float(os.getenv('IMAP_RETRY_DELAY', '1.0'))
               },
               'production': {
                   'pool_size': int(os.getenv('IMAP_POOL_SIZE', '5')),
                   'max_connections': int(os.getenv('IMAP_MAX_CONNECTIONS', '20')),
                   'health_check_interval': float(os.getenv('HEALTH_CHECK_INTERVAL', '60.0')),
                   'metrics_interval': float(os.getenv('METRICS_INTERVAL', '30.0')),
                   'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                   'log_file': os.getenv('LOG_FILE', '/var/log/imap-service.log')
               }
           }
   
       def validate_configuration(self, config: Dict[str, Any]):
           """
           Validate production configuration.
           """
           required_keys = ['imap', 'production']
           for key in required_keys:
               if key not in config:
                   raise ValueError(f"Missing required configuration section: {key}")
           
           imap_config = config['imap']
           required_imap_keys = ['host', 'username', 'password']
           for key in required_imap_keys:
               if not imap_config.get(key):
                   raise ValueError(f"Missing required IMAP configuration: {key}")
   
       def get_default_configuration(self) -> Dict[str, Any]:
           """
           Get default production configuration.
           """
           return {
               'imap': {
                   'host': 'imap.gmail.com',
                   'port': 993,
                   'username': 'service@example.com',
                   'password': 'secure_password',
                   'use_ssl': True,
                   'timeout': 30.0,
                   'max_retries': 3,
                   'retry_delay': 1.0
               },
               'production': {
                   'pool_size': 5,
                   'max_connections': 20,
                   'health_check_interval': 60.0,
                   'metrics_interval': 30.0,
                   'log_level': 'INFO',
                   'log_file': '/var/log/imap-service.log'
               }
           }
   
       def setup_production_logging(self):
           """
           Setup production-grade logging.
           """
           # Create logs directory
           log_file = self.config.get('production', {}).get('log_file', '/var/log/imap-service.log')
           log_dir = os.path.dirname(log_file)
           os.makedirs(log_dir, exist_ok=True)
           
           # Configure root logger
           root_logger = logging.getLogger()
           log_level = getattr(logging, self.config.get('production', {}).get('log_level', 'INFO'))
           root_logger.setLevel(log_level)
           
           # Remove existing handlers
           for handler in root_logger.handlers[:]:
               root_logger.removeHandler(handler)
           
           # File handler with rotation
           file_handler = logging.handlers.RotatingFileHandler(
               log_file,
               maxBytes=100 * 1024 * 1024,  # 100MB
               backupCount=10
           )
           
           # Console handler
           console_handler = logging.StreamHandler()
           
           # Formatter
           formatter = logging.Formatter(
               '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
           )
           
           file_handler.setFormatter(formatter)
           console_handler.setFormatter(formatter)
           
           root_logger.addHandler(file_handler)
           root_logger.addHandler(console_handler)
   
       def setup_signal_handlers(self):
           """
           Setup graceful shutdown signal handlers.
           """
           def signal_handler(signum, frame):
               self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
               self.shutdown_event.set()
           
           signal.signal(signal.SIGTERM, signal_handler)
           signal.signal(signal.SIGINT, signal_handler)
   
       def start_production_service(self):
           """
           Start the production service with all components.
           """
           try:
               self.logger.info("Starting production IMAP service...")
               
               # Start health monitor
               self.health_monitor.start()
               
               # Start metrics collection
               self.metrics.start()
               
               # Main service loop
               self.run_service_loop()
               
           except Exception as e:
               self.logger.error(f"Production service failed: {e}")
               raise
           finally:
               self.cleanup()
   
       def run_service_loop(self):
           """
           Main service loop.
           """
           self.logger.info("Production service loop started")
           
           while not self.shutdown_event.is_set():
               try:
                   # Main service operations
                   self.process_mailbox_operations()
                   
                   # Brief pause
                   time.sleep(1.0)
                   
               except Exception as e:
                   self.logger.error(f"Service loop error: {e}")
                   self.metrics.increment('service_errors')
                   
                   # Continue after error
                   time.sleep(5.0)
           
           self.logger.info("Service loop shutting down")
   
       def process_mailbox_operations(self):
           """
           Process mailbox operations with production patterns.
           """
           try:
               with self.connection_pool.get_connection() as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Get unprocessed messages
                   unprocessed = uid_service.create_message_set_from_search(
                       IMAPSearchCriteria.UNSEEN
                   )
                   
                   if not unprocessed.is_empty():
                       self.logger.info(f"Processing {len(unprocessed)} unprocessed messages")
                       
                       # Process in batches
                       for batch in unprocessed.iter_batches(batch_size=50):
                           self.process_message_batch(uid_service, batch)
                           
                           # Check for shutdown
                           if self.shutdown_event.is_set():
                               break
                   
                   self.metrics.increment('mailbox_operations')
                   
           except Exception as e:
               self.logger.error(f"Mailbox operation failed: {e}")
               self.metrics.increment('operation_errors')
               raise
   
       def process_message_batch(self, uid_service: IMAPMailboxUIDService, batch: MessageSet):
           """
           Process a batch of messages with error handling.
           """
           try:
               # Fetch messages
               fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   for message in messages:
                       try:
                           self.process_single_message(message)
                           self.metrics.increment('messages_processed')
                       except Exception as e:
                           self.logger.error(f"Failed to process message {message.uid}: {e}")
                           self.metrics.increment('message_errors')
               else:
                   self.logger.error(f"Failed to fetch batch: {fetch_result.error_message}")
                   self.metrics.increment('fetch_errors')
                   
           except Exception as e:
               self.logger.error(f"Batch processing failed: {e}")
               self.metrics.increment('batch_errors')
   
       def process_single_message(self, message):
           """
           Process a single message.
           """
           # Simulate message processing
           self.logger.debug(f"Processing message: {message.subject}")
           
           # Business logic would go here
           time.sleep(0.01)  # Simulate processing time
   
       def cleanup(self):
           """
           Cleanup resources during shutdown.
           """
           self.logger.info("Cleaning up production service...")
           
           try:
               # Stop health monitor
               self.health_monitor.stop()
               
               # Stop metrics
               self.metrics.stop()
               
               # Close connection pool
               self.connection_pool.close()
               
           except Exception as e:
               self.logger.error(f"Cleanup error: {e}")
           
           self.logger.info("Production service cleanup completed")


   class ProductionMetrics:
       """
       Production metrics collection.
       """
       
       def __init__(self):
           self.metrics = {}
           self.start_time = time.time()
           self.logger = logging.getLogger(f"{__name__}.metrics")
           self.running = False
           self.metrics_thread = None
   
       def start(self):
           """
           Start metrics collection.
           """
           self.running = True
           self.metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
           self.metrics_thread.start()
           self.logger.info("Metrics collection started")
   
       def stop(self):
           """
           Stop metrics collection.
           """
           self.running = False
           if self.metrics_thread:
               self.metrics_thread.join(timeout=5.0)
           self.logger.info("Metrics collection stopped")
   
       def increment(self, metric_name: str, value: int = 1):
           """
           Increment a metric counter.
           """
           self.metrics[metric_name] = self.metrics.get(metric_name, 0) + value
   
       def gauge(self, metric_name: str, value: float):
           """
           Set a gauge metric value.
           """
           self.metrics[metric_name] = value
   
       def get_metrics(self) -> Dict[str, Any]:
           """
           Get current metrics.
           """
           uptime = time.time() - self.start_time
           
           return {
               'uptime_seconds': uptime,
               'timestamp': datetime.now().isoformat(),
               'metrics': self.metrics.copy()
           }
   
       def _metrics_loop(self):
           """
           Metrics collection loop.
           """
           while self.running:
               try:
                   # Log metrics periodically
                   metrics = self.get_metrics()
                   self.logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
                   
                   # Sleep for metrics interval
                   time.sleep(30.0)
                   
               except Exception as e:
                   self.logger.error(f"Metrics loop error: {e}")


   class HealthMonitor:
       """
       Production health monitoring.
       """
       
       def __init__(self, service: ProductionIMAPService):
           self.service = service
           self.logger = logging.getLogger(f"{__name__}.health")
           self.running = False
           self.health_thread = None
           self.last_health_check = None
   
       def start(self):
           """
           Start health monitoring.
           """
           self.running = True
           self.health_thread = threading.Thread(target=self._health_loop, daemon=True)
           self.health_thread.start()
           self.logger.info("Health monitoring started")
   
       def stop(self):
           """
           Stop health monitoring.
           """
           self.running = False
           if self.health_thread:
               self.health_thread.join(timeout=5.0)
           self.logger.info("Health monitoring stopped")
   
       def check_health(self) -> Dict[str, Any]:
           """
           Perform health check.
           """
           health_status = {
               'status': 'healthy',
               'timestamp': datetime.now().isoformat(),
               'checks': {}
           }
           
           try:
               # Check connection pool
               pool_health = self.service.connection_pool.health_check()
               health_status['checks']['connection_pool'] = pool_health
               
               # Check metrics system
               metrics_health = self.service.metrics.get_metrics()
               health_status['checks']['metrics'] = {
                   'status': 'healthy',
                   'uptime': metrics_health['uptime_seconds']
               }
               
               # Overall status
               if not pool_health.get('healthy', False):
                   health_status['status'] = 'unhealthy'
               
           except Exception as e:
               health_status['status'] = 'unhealthy'
               health_status['error'] = str(e)
               self.logger.error(f"Health check failed: {e}")
           
           self.last_health_check = health_status
           return health_status
   
       def _health_loop(self):
           """
           Health monitoring loop.
           """
           while self.running:
               try:
                   health = self.check_health()
                   
                   if health['status'] == 'unhealthy':
                       self.logger.warning(f"Health check failed: {health}")
                   else:
                       self.logger.debug("Health check passed")
                   
                   # Sleep for health check interval
                   time.sleep(60.0)
                   
               except Exception as e:
                   self.logger.error(f"Health monitoring error: {e}")


   class ConnectionPool:
       """
       Production connection pool.
       """
       
       def __init__(self, config: Dict[str, Any]):
           self.config = config['imap']
           self.pool_config = config['production']
           self.logger = logging.getLogger(f"{__name__}.pool")
           
           # Connection pool
           self.pool = []
           self.pool_lock = threading.Lock()
           self.max_connections = self.pool_config['max_connections']
           self.pool_size = self.pool_config['pool_size']
           
           # Initialize pool
           self._initialize_pool()
   
       def _initialize_pool(self):
           """
           Initialize the connection pool.
           """
           try:
               for i in range(self.pool_size):
                   client = self._create_client()
                   self.pool.append(client)
               
               self.logger.info(f"Connection pool initialized with {len(self.pool)} connections")
               
           except Exception as e:
               self.logger.error(f"Failed to initialize connection pool: {e}")
               raise
   
       def _create_client(self) -> IMAPClient:
           """
           Create a new IMAP client.
           """
           config = ConnectionConfig(
               host=self.config['host'],
               port=self.config['port'],
               username=self.config['username'],
               password=self.config['password'],
               use_ssl=self.config['use_ssl'],
               timeout=self.config['timeout'],
               max_retries=self.config['max_retries'],
               retry_delay=self.config['retry_delay'],
               enable_monitoring=True
           )
           
           return IMAPClient(config=config)
   
       def get_connection(self):
           """
           Get a connection from the pool.
           """
           return PooledConnection(self)
   
       def _acquire_connection(self) -> IMAPClient:
           """
           Acquire a connection from the pool.
           """
           with self.pool_lock:
               if self.pool:
                   client = self.pool.pop()
                   self.logger.debug("Acquired connection from pool")
                   return client
               else:
                   # Create new connection if pool is empty
                   client = self._create_client()
                   self.logger.debug("Created new connection (pool empty)")
                   return client
   
       def _release_connection(self, client: IMAPClient):
           """
           Release a connection back to the pool.
           """
           with self.pool_lock:
               if len(self.pool) < self.pool_size:
                   self.pool.append(client)
                   self.logger.debug("Released connection to pool")
               else:
                   # Close excess connections
                   try:
                       client.disconnect()
                       self.logger.debug("Closed excess connection")
                   except Exception as e:
                       self.logger.warning(f"Error closing excess connection: {e}")
   
       def health_check(self) -> Dict[str, Any]:
           """
           Check pool health.
           """
           with self.pool_lock:
               pool_status = {
                   'healthy': True,
                   'pool_size': len(self.pool),
                   'max_connections': self.max_connections,
                   'target_pool_size': self.pool_size
               }
               
               # Check if pool is too small
               if len(self.pool) < self.pool_size // 2:
                   pool_status['healthy'] = False
                   pool_status['warning'] = 'Pool size below 50% of target'
               
               return pool_status
   
       def close(self):
           """
           Close all connections in the pool.
           """
           with self.pool_lock:
               for client in self.pool:
                   try:
                       client.disconnect()
                   except Exception as e:
                       self.logger.warning(f"Error closing pooled connection: {e}")
               
               self.pool.clear()
               self.logger.info("Connection pool closed")


   class PooledConnection:
       """
       Context manager for pooled connections.
       """
       
       def __init__(self, pool: ConnectionPool):
           self.pool = pool
           self.client = None
   
       def __enter__(self) -> IMAPClient:
           self.client = self.pool._acquire_connection()
           self.client.connect()
           return self.client
   
       def __exit__(self, exc_type, exc_val, exc_tb):
           if self.client:
               try:
                   if exc_type is None:
                       # No exception, return to pool
                       self.pool._release_connection(self.client)
                   else:
                       # Exception occurred, close connection
                       self.client.disconnect()
               except Exception as e:
                   logging.warning(f"Error handling pooled connection: {e}")


   class ConfigurationManager:
       """
       Production configuration management.
       """
       
       @staticmethod
       def load_production_config(config_path: str) -> Dict[str, Any]:
           """
           Load production configuration with validation.
           """
           if not os.path.exists(config_path):
               raise FileNotFoundError(f"Configuration file not found: {config_path}")
           
           with open(config_path, 'r') as f:
               config = json.load(f)
           
           # Validate configuration
           ConfigurationManager.validate_config(config)
           
           return config
   
       @staticmethod
       def validate_config(config: Dict[str, Any]):
           """
           Validate configuration structure.
           """
           required_sections = ['imap', 'production']
           for section in required_sections:
               if section not in config:
                   raise ValueError(f"Missing configuration section: {section}")
           
           # Validate IMAP config
           imap_config = config['imap']
           required_imap = ['host', 'username', 'password']
           for key in required_imap:
               if not imap_config.get(key):
                   raise ValueError(f"Missing IMAP configuration: {key}")
   
       @staticmethod
       def create_sample_config(output_path: str):
           """
           Create a sample production configuration file.
           """
           sample_config = {
               "imap": {
                   "host": "imap.gmail.com",
                   "port": 993,
                   "username": "service@example.com",
                   "password": "secure_password",
                   "use_ssl": True,
                   "timeout": 30.0,
                   "max_retries": 3,
                   "retry_delay": 1.0
               },
               "production": {
                   "pool_size": 5,
                   "max_connections": 20,
                   "health_check_interval": 60.0,
                   "metrics_interval": 30.0,
                   "log_level": "INFO",
                   "log_file": "/var/log/imap-service.log"
               }
           }
           
           with open(output_path, 'w') as f:
               json.dump(sample_config, f, indent=2)


   def main():
       """
       Main function to run the production service.
       """
       # Check for configuration file
       config_path = os.getenv('IMAP_CONFIG_PATH', 'config/production.json')
       
       if not os.path.exists(config_path):
           print(f"Configuration file not found: {config_path}")
           print("Creating sample configuration...")
           
           os.makedirs(os.path.dirname(config_path), exist_ok=True)
           ConfigurationManager.create_sample_config(config_path)
           
           print(f"Sample configuration created at: {config_path}")
           print("Please edit the configuration file with your IMAP settings.")
           return 1
       
       try:
           # Create and start production service
           service = ProductionIMAPService(config_path)
           service.start_production_service()
           
       except KeyboardInterrupt:
           print("\nReceived interrupt signal, shutting down...")
           return 0
       except Exception as e:
           logging.error(f"Production service failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Production Configuration
------------------------

Configuration File
~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "imap": {
       "host": "imap.company.com",
       "port": 993,
       "username": "service@company.com",
       "password": "secure_password",
       "use_ssl": true,
       "timeout": 30.0,
       "max_retries": 3,
       "retry_delay": 1.0
     },
     "production": {
       "pool_size": 10,
       "max_connections": 50,
       "health_check_interval": 60.0,
       "metrics_interval": 30.0,
       "log_level": "INFO",
       "log_file": "/var/log/imap-service.log"
     }
   }

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # IMAP Configuration
   export IMAP_HOST="imap.company.com"
   export IMAP_USERNAME="service@company.com"
   export IMAP_PASSWORD="secure_password"
   export IMAP_POOL_SIZE="10"
   export IMAP_MAX_CONNECTIONS="50"
   
   # Logging
   export LOG_LEVEL="INFO"
   export LOG_FILE="/var/log/imap-service.log"
   
   # Health Checks
   export HEALTH_CHECK_INTERVAL="60.0"
   export METRICS_INTERVAL="30.0"

Docker Deployment
~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   # Create non-root user
   RUN useradd -m -u 1000 imapuser
   USER imapuser
   
   # Health check
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
     CMD python -c "import requests; requests.get('http://localhost:8080/health')"
   
   CMD ["python", "production_service.py"]

Kubernetes Deployment
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: imap-service
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: imap-service
     template:
       metadata:
         labels:
           app: imap-service
       spec:
         containers:
         - name: imap-service
           image: your-registry/imap-service:latest
           ports:
           - containerPort: 8080
           env:
           - name: IMAP_HOST
             valueFrom:
               secretKeyRef:
                 name: imap-secrets
                 key: host
           - name: IMAP_USERNAME
             valueFrom:
               secretKeyRef:
                 name: imap-secrets
                 key: username
           - name: IMAP_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: imap-secrets
                 key: password
           livenessProbe:
             httpGet:
               path: /health
               port: 8080
             initialDelaySeconds: 30
             periodSeconds: 30
           readinessProbe:
             httpGet:
               path: /ready
               port: 8080
             initialDelaySeconds: 5
             periodSeconds: 10

Monitoring and Metrics
----------------------

Prometheus Metrics
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from prometheus_client import Counter, Histogram, Gauge, start_http_server
   
   # Metrics
   messages_processed = Counter('imap_messages_processed_total', 'Total processed messages')
   operation_duration = Histogram('imap_operation_duration_seconds', 'Operation duration')
   active_connections = Gauge('imap_active_connections', 'Active IMAP connections')
   
   # Start metrics server
   start_http_server(8080)

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging.config
   
   LOGGING_CONFIG = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'detailed': {
               'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
           },
           'json': {
               'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
           }
       },
       'handlers': {
           'file': {
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/var/log/imap-service.log',
               'maxBytes': 100 * 1024 * 1024,
               'backupCount': 10,
               'formatter': 'detailed'
           },
           'console': {
               'class': 'logging.StreamHandler',
               'formatter': 'json'
           }
       },
       'root': {
           'level': 'INFO',
           'handlers': ['file', 'console']
       }
   }
   
   logging.config.dictConfig(LOGGING_CONFIG)

Health Checks
~~~~~~~~~~~~~

.. code-block:: python

   def health_check():
       """
       Comprehensive health check.
       """
       checks = {
           'database': check_database_connection(),
           'imap': check_imap_connection(),
           'memory': check_memory_usage(),
           'disk': check_disk_space()
       }
       
       overall_status = all(checks.values())
       
       return {
           'status': 'healthy' if overall_status else 'unhealthy',
           'checks': checks,
           'timestamp': datetime.now().isoformat()
       }

Best Practices
--------------

✅ **DO:**

- Use connection pooling for better performance

- Implement comprehensive logging

- Monitor health and metrics

- Use configuration files or environment variables

- Handle graceful shutdown

- Implement retry logic with exponential backoff

- Use TLS/SSL for all connections

- Validate all configuration

- Implement circuit breakers for external dependencies

❌ **DON'T:**

- Hardcode credentials in source code

- Ignore error handling

- Skip health checks

- Use blocking operations without timeouts

- Ignore resource cleanup

- Deploy without monitoring

- Skip configuration validation

- Use plain text passwords

- Ignore connection limits

Security Considerations
-----------------------

Credentials Management
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use environment variables
   username = os.getenv('IMAP_USERNAME')
   password = os.getenv('IMAP_PASSWORD')
   
   # Or use secret management systems
   from kubernetes import client, config
   
   def get_secret(name, key):
       config.load_incluster_config()
       v1 = client.CoreV1Api()
       secret = v1.read_namespaced_secret(name, 'default')
       return secret.data[key].decode('base64')

Network Security
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Always use TLS
   config = ConnectionConfig(
       host='imap.company.com',
       port=993,
       use_ssl=True,
       verify_ssl=True
   )
   
   # Configure timeouts
   config.timeout = 30.0
   config.read_timeout = 60.0

Performance Optimization
------------------------

Connection Pooling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimal pool configuration
   pool_config = {
       'pool_size': 10,           # Base pool size
       'max_connections': 50,     # Maximum connections
       'timeout': 30.0,           # Connection timeout
       'idle_timeout': 300.0,     # Idle connection timeout
       'max_retries': 3           # Retry attempts
   }

Caching Strategy
~~~~~~~~~~~~~~~~

.. code-block:: python

   import redis
   
   # Redis cache for search results
   cache = redis.Redis(host='redis-server', port=6379, db=0)
   
   def cached_search(criteria, cache_key, ttl=300):
       # Check cache first
       cached_result = cache.get(cache_key)
       if cached_result:
           return json.loads(cached_result)
       
       # Perform search
       result = uid_service.create_message_set_from_search(criteria)
       
       # Cache result
       cache.setex(cache_key, ttl, json.dumps(list(result.parsed_ids)))
       
       return result

Scaling Patterns
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Horizontal scaling with load balancing
   class LoadBalancedIMAPService:
       def __init__(self, servers):
           self.servers = servers
           self.current_server = 0
       
       def get_next_server(self):
           server = self.servers[self.current_server]
           self.current_server = (self.current_server + 1) % len(self.servers)
           return server

Next Steps
----------

For more advanced patterns, see:

- :doc:`monitoring_analytics` - Monitoring and analytics
- :doc:`error_handling` - Error handling strategies
- :doc:`large_volume_handling` - High-performance processing
- :doc:`client_advanced` - Advanced client features 