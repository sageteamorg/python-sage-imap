.. _error_handling:

Error Handling Strategies
==========================

This example demonstrates comprehensive error handling strategies for robust IMAP operations including exception handling, retry logic, circuit breakers, and graceful degradation.

**⚠️ IMPORTANT: This example covers production-grade error handling patterns!**

Overview
--------

You'll learn how to:

- Handle IMAP-specific exceptions
- Implement retry logic with exponential backoff
- Use circuit breaker patterns
- Implement graceful degradation
- Handle network timeouts and failures
- Recover from connection issues
- Log and monitor errors effectively
- Implement fallback strategies

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Understanding of exception handling
- Knowledge of resilience patterns

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Error Handling Strategies Example
   
   This example demonstrates comprehensive error handling strategies
   for robust IMAP operations in production environments.
   """
   
   import logging
   import time
   import random
   from datetime import datetime, timedelta
   from typing import Dict, List, Optional, Any, Callable
   from enum import Enum
   from dataclasses import dataclass
   from functools import wraps
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.exceptions import (
       IMAPConnectionError,
       IMAPOperationError,
       IMAPAuthenticationError,
       IMAPTimeoutError
   )
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class ErrorType(Enum):
       """Error classification for handling strategies."""
       CONNECTION = "connection"
       AUTHENTICATION = "authentication"
       OPERATION = "operation"
       TIMEOUT = "timeout"
       NETWORK = "network"
       TEMPORARY = "temporary"
       PERMANENT = "permanent"
   
   
   @dataclass
   class ErrorContext:
       """Context information for error handling."""
       error_type: ErrorType
       exception: Exception
       operation: str
       attempt: int
       max_attempts: int
       timestamp: datetime
       metadata: Dict[str, Any]
   
   
   class CircuitBreakerState(Enum):
       """Circuit breaker states."""
       CLOSED = "closed"
       OPEN = "open"
       HALF_OPEN = "half_open"
   
   
   class CircuitBreaker:
       """
       Circuit breaker implementation for IMAP operations.
       """
       
       def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
           self.failure_threshold = failure_threshold
           self.recovery_timeout = recovery_timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = CircuitBreakerState.CLOSED
           self.logger = logging.getLogger(f"{__name__}.circuit_breaker")
       
       def call(self, func: Callable, *args, **kwargs):
           """
           Execute function with circuit breaker protection.
           """
           if self.state == CircuitBreakerState.OPEN:
               if self._should_attempt_reset():
                   self.state = CircuitBreakerState.HALF_OPEN
                   self.logger.info("Circuit breaker transitioning to HALF_OPEN")
               else:
                   raise Exception("Circuit breaker is OPEN")
           
           try:
               result = func(*args, **kwargs)
               self._on_success()
               return result
           except Exception as e:
               self._on_failure()
               raise
       
       def _should_attempt_reset(self) -> bool:
           """Check if circuit breaker should attempt reset."""
           if self.last_failure_time is None:
               return True
           
           time_since_failure = time.time() - self.last_failure_time
           return time_since_failure >= self.recovery_timeout
       
       def _on_success(self):
           """Handle successful operation."""
           self.failure_count = 0
           if self.state == CircuitBreakerState.HALF_OPEN:
               self.state = CircuitBreakerState.CLOSED
               self.logger.info("Circuit breaker reset to CLOSED")
       
       def _on_failure(self):
           """Handle failed operation."""
           self.failure_count += 1
           self.last_failure_time = time.time()
           
           if self.failure_count >= self.failure_threshold:
               self.state = CircuitBreakerState.OPEN
               self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
   
   
   class RetryStrategy:
       """
       Retry strategy with exponential backoff.
       """
       
       def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                    max_delay: float = 60.0, exponential_base: float = 2.0):
           self.max_attempts = max_attempts
           self.base_delay = base_delay
           self.max_delay = max_delay
           self.exponential_base = exponential_base
       
       def get_delay(self, attempt: int) -> float:
           """Calculate delay for given attempt."""
           if attempt <= 0:
               return 0
           
           delay = self.base_delay * (self.exponential_base ** (attempt - 1))
           # Add jitter to prevent thundering herd
           jitter = random.uniform(0, 0.1) * delay
           return min(delay + jitter, self.max_delay)
       
       def should_retry(self, error_context: ErrorContext) -> bool:
           """Determine if operation should be retried."""
           if error_context.attempt >= self.max_attempts:
               return False
           
           # Don't retry authentication errors
           if error_context.error_type == ErrorType.AUTHENTICATION:
               return False
           
           # Don't retry permanent errors
           if error_context.error_type == ErrorType.PERMANENT:
               return False
           
           return True
   
   
   class ErrorHandlingExample:
       """
       Comprehensive error handling example.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize error handling example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
           # Error handling components
           self.circuit_breaker = CircuitBreaker()
           self.retry_strategy = RetryStrategy()
           self.error_stats = {
               'total_errors': 0,
               'error_types': {},
               'retry_counts': {},
               'circuit_breaker_trips': 0
           }
       
       def demonstrate_error_handling(self):
           """
           Demonstrate comprehensive error handling strategies.
           """
           logger.info("=== Error Handling Strategies Example ===")
           
           try:
               # Exception classification
               self.demonstrate_exception_classification()
               
               # Retry strategies
               self.demonstrate_retry_strategies()
               
               # Circuit breaker patterns
               self.demonstrate_circuit_breaker()
               
               # Graceful degradation
               self.demonstrate_graceful_degradation()
               
               # Connection recovery
               self.demonstrate_connection_recovery()
               
               # Error monitoring
               self.demonstrate_error_monitoring()
               
               # Fallback strategies
               self.demonstrate_fallback_strategies()
               
               # Error reporting
               self.generate_error_report()
               
               logger.info("✓ Error handling strategies completed successfully")
               
           except Exception as e:
               logger.error(f"❌ Error handling demonstration failed: {e}")
               raise
       
       def demonstrate_exception_classification(self):
           """
           Demonstrate classification of different exception types.
           """
           logger.info("--- Exception Classification ---")
           
           try:
               # Simulate different types of errors
               error_scenarios = [
                   ("Connection Error", self.simulate_connection_error),
                   ("Authentication Error", self.simulate_authentication_error),
                   ("Timeout Error", self.simulate_timeout_error),
                   ("Operation Error", self.simulate_operation_error),
                   ("Network Error", self.simulate_network_error)
               ]
               
               for error_name, error_func in error_scenarios:
                   try:
                       logger.info(f"  Testing {error_name}...")
                       error_func()
                   except Exception as e:
                       error_type = self.classify_error(e)
                       logger.info(f"    • Classification: {error_type.value}")
                       logger.info(f"    • Exception: {type(e).__name__}")
                       logger.info(f"    • Message: {str(e)}")
                       
                       # Update statistics
                       self.error_stats['total_errors'] += 1
                       self.error_stats['error_types'][error_type.value] = \
                           self.error_stats['error_types'].get(error_type.value, 0) + 1
               
               logger.info("✓ Exception classification completed")
               
           except Exception as e:
               logger.error(f"Failed exception classification: {e}")
       
       def classify_error(self, exception: Exception) -> ErrorType:
           """
           Classify an exception into error type.
           """
           if isinstance(exception, IMAPConnectionError):
               return ErrorType.CONNECTION
           elif isinstance(exception, IMAPAuthenticationError):
               return ErrorType.AUTHENTICATION
           elif isinstance(exception, IMAPTimeoutError):
               return ErrorType.TIMEOUT
           elif isinstance(exception, IMAPOperationError):
               return ErrorType.OPERATION
           elif "network" in str(exception).lower():
               return ErrorType.NETWORK
           elif "temporary" in str(exception).lower():
               return ErrorType.TEMPORARY
           else:
               return ErrorType.PERMANENT
       
       def simulate_connection_error(self):
           """Simulate connection error."""
           raise IMAPConnectionError("Connection refused")
       
       def simulate_authentication_error(self):
           """Simulate authentication error."""
           raise IMAPAuthenticationError("Invalid credentials")
       
       def simulate_timeout_error(self):
           """Simulate timeout error."""
           raise IMAPTimeoutError("Operation timed out")
       
       def simulate_operation_error(self):
           """Simulate operation error."""
           raise IMAPOperationError("Invalid mailbox")
       
       def simulate_network_error(self):
           """Simulate network error."""
           raise ConnectionError("Network unreachable")
       
       def demonstrate_retry_strategies(self):
           """
           Demonstrate retry strategies with exponential backoff.
           """
           logger.info("--- Retry Strategies ---")
           
           try:
               # Test retry with different error types
               test_operations = [
                   ("Temporary failure", self.create_temporary_failure_operation()),
                   ("Permanent failure", self.create_permanent_failure_operation()),
                   ("Authentication failure", self.create_auth_failure_operation()),
                   ("Eventual success", self.create_eventual_success_operation())
               ]
               
               for op_name, operation in test_operations:
                   logger.info(f"  Testing {op_name}...")
                   
                   try:
                       result = self.execute_with_retry(operation, op_name)
                       logger.info(f"    ✓ Operation succeeded: {result}")
                   except Exception as e:
                       logger.info(f"    ❌ Operation failed after retries: {e}")
               
               logger.info("✓ Retry strategies completed")
               
           except Exception as e:
               logger.error(f"Failed retry strategies: {e}")
       
       def create_temporary_failure_operation(self):
           """Create operation that fails temporarily."""
           def operation():
               raise IMAPOperationError("Temporary server error")
           return operation
       
       def create_permanent_failure_operation(self):
           """Create operation that fails permanently."""
           def operation():
               raise IMAPAuthenticationError("Invalid credentials")
           return operation
       
       def create_auth_failure_operation(self):
           """Create operation that fails with authentication error."""
           def operation():
               raise IMAPAuthenticationError("Authentication failed")
           return operation
       
       def create_eventual_success_operation(self):
           """Create operation that succeeds after retries."""
           attempts = {'count': 0}
           
           def operation():
               attempts['count'] += 1
               if attempts['count'] < 3:
                   raise IMAPConnectionError("Connection failed")
               return "Success after retries"
           
           return operation
       
       def execute_with_retry(self, operation: Callable, operation_name: str):
           """
           Execute operation with retry logic.
           """
           for attempt in range(1, self.retry_strategy.max_attempts + 1):
               try:
                   return operation()
               except Exception as e:
                   error_type = self.classify_error(e)
                   error_context = ErrorContext(
                       error_type=error_type,
                       exception=e,
                       operation=operation_name,
                       attempt=attempt,
                       max_attempts=self.retry_strategy.max_attempts,
                       timestamp=datetime.now(),
                       metadata={}
                   )
                   
                   if self.retry_strategy.should_retry(error_context):
                       delay = self.retry_strategy.get_delay(attempt)
                       logger.info(f"    Attempt {attempt} failed: {e}")
                       logger.info(f"    Retrying in {delay:.2f}s...")
                       time.sleep(delay)
                       
                       # Update retry statistics
                       self.error_stats['retry_counts'][operation_name] = \
                           self.error_stats['retry_counts'].get(operation_name, 0) + 1
                   else:
                       logger.info(f"    Not retrying {error_type.value} error")
                       raise
           
           raise Exception(f"Operation failed after {self.retry_strategy.max_attempts} attempts")
       
       def demonstrate_circuit_breaker(self):
           """
           Demonstrate circuit breaker pattern.
           """
           logger.info("--- Circuit Breaker Pattern ---")
           
           try:
               # Create failing operation
               failure_operation = self.create_always_failing_operation()
               
               # Test circuit breaker behavior
               logger.info("  Testing circuit breaker with failing operation...")
               
               for i in range(10):
                   try:
                       result = self.circuit_breaker.call(failure_operation)
                       logger.info(f"    Attempt {i+1}: Success - {result}")
                   except Exception as e:
                       logger.info(f"    Attempt {i+1}: Failed - {e}")
                       
                       if self.circuit_breaker.state == CircuitBreakerState.OPEN:
                           logger.info("    Circuit breaker is now OPEN")
                           self.error_stats['circuit_breaker_trips'] += 1
                           break
                   
                   time.sleep(0.1)
               
               # Test recovery
               logger.info("  Testing circuit breaker recovery...")
               
               # Wait for recovery timeout (simulate)
               logger.info("  Simulating recovery timeout...")
               time.sleep(1.0)
               
               # Create successful operation
               success_operation = self.create_success_operation()
               
               try:
                   result = self.circuit_breaker.call(success_operation)
                   logger.info(f"    Recovery attempt: Success - {result}")
               except Exception as e:
                   logger.info(f"    Recovery attempt: Failed - {e}")
               
               logger.info("✓ Circuit breaker demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed circuit breaker demonstration: {e}")
       
       def create_always_failing_operation(self):
           """Create operation that always fails."""
           def operation():
               raise IMAPConnectionError("Persistent connection failure")
           return operation
       
       def create_success_operation(self):
           """Create operation that always succeeds."""
           def operation():
               return "Operation successful"
           return operation
       
       def demonstrate_graceful_degradation(self):
           """
           Demonstrate graceful degradation strategies.
           """
           logger.info("--- Graceful Degradation ---")
           
           try:
               # Test graceful degradation scenarios
               scenarios = [
                   ("Full service", self.full_service_operation),
                   ("Limited service", self.limited_service_operation),
                   ("Cache-only service", self.cache_only_service_operation),
                   ("Offline mode", self.offline_mode_operation)
               ]
               
               for scenario_name, operation in scenarios:
                   try:
                       logger.info(f"  Testing {scenario_name}...")
                       result = operation()
                       logger.info(f"    ✓ {scenario_name}: {result}")
                   except Exception as e:
                       logger.info(f"    ❌ {scenario_name}: {e}")
               
               logger.info("✓ Graceful degradation completed")
               
           except Exception as e:
               logger.error(f"Failed graceful degradation: {e}")
       
       def full_service_operation(self):
           """Full service operation (may fail)."""
           # Simulate occasional failure
           if random.random() < 0.3:
               raise IMAPConnectionError("Connection failed")
           return "Full service available"
       
       def limited_service_operation(self):
           """Limited service operation (more reliable)."""
           # Simulate higher success rate
           if random.random() < 0.1:
               raise IMAPOperationError("Limited service error")
           return "Limited service available"
       
       def cache_only_service_operation(self):
           """Cache-only service operation (very reliable)."""
           return "Cache-only service available"
       
       def offline_mode_operation(self):
           """Offline mode operation (always available)."""
           return "Offline mode available"
       
       def demonstrate_connection_recovery(self):
           """
           Demonstrate connection recovery strategies.
           """
           logger.info("--- Connection Recovery ---")
           
           try:
               # Simulate connection recovery
               recovery_strategies = [
                   ("Immediate reconnection", self.immediate_reconnection),
                   ("Delayed reconnection", self.delayed_reconnection),
                   ("Exponential backoff", self.exponential_backoff_reconnection),
                   ("Connection pool recovery", self.pool_recovery)
               ]
               
               for strategy_name, strategy in recovery_strategies:
                   try:
                       logger.info(f"  Testing {strategy_name}...")
                       result = strategy()
                       logger.info(f"    ✓ {strategy_name}: {result}")
                   except Exception as e:
                       logger.info(f"    ❌ {strategy_name}: {e}")
               
               logger.info("✓ Connection recovery completed")
               
           except Exception as e:
               logger.error(f"Failed connection recovery: {e}")
       
       def immediate_reconnection(self):
           """Immediate reconnection strategy."""
           # Simulate immediate reconnection
           time.sleep(0.1)
           return "Immediate reconnection successful"
       
       def delayed_reconnection(self):
           """Delayed reconnection strategy."""
           # Simulate delayed reconnection
           time.sleep(0.5)
           return "Delayed reconnection successful"
       
       def exponential_backoff_reconnection(self):
           """Exponential backoff reconnection strategy."""
           # Simulate exponential backoff
           delays = [0.1, 0.2, 0.4, 0.8]
           for delay in delays:
               time.sleep(delay)
               # Simulate connection attempt
               if random.random() > 0.5:
                   return f"Exponential backoff successful after {delay}s"
           
           raise Exception("Exponential backoff failed")
       
       def pool_recovery(self):
           """Connection pool recovery strategy."""
           # Simulate pool recovery
           time.sleep(0.3)
           return "Connection pool recovery successful"
       
       def demonstrate_error_monitoring(self):
           """
           Demonstrate error monitoring and alerting.
           """
           logger.info("--- Error Monitoring ---")
           
           try:
               # Simulate error monitoring
               monitoring_checks = [
                   ("Error rate check", self.check_error_rate),
                   ("Circuit breaker status", self.check_circuit_breaker_status),
                   ("Connection health", self.check_connection_health),
                   ("Performance metrics", self.check_performance_metrics)
               ]
               
               for check_name, check_func in monitoring_checks:
                   try:
                       logger.info(f"  Running {check_name}...")
                       result = check_func()
                       logger.info(f"    ✓ {check_name}: {result}")
                   except Exception as e:
                       logger.info(f"    ❌ {check_name}: {e}")
               
               logger.info("✓ Error monitoring completed")
               
           except Exception as e:
               logger.error(f"Failed error monitoring: {e}")
       
       def check_error_rate(self):
           """Check current error rate."""
           error_rate = self.error_stats['total_errors'] / max(1, time.time() - time.time() + 60)
           if error_rate > 0.1:
               return f"WARNING: High error rate {error_rate:.2f}/min"
           return f"Error rate normal: {error_rate:.2f}/min"
       
       def check_circuit_breaker_status(self):
           """Check circuit breaker status."""
           if self.circuit_breaker.state == CircuitBreakerState.OPEN:
               return "WARNING: Circuit breaker is OPEN"
           return f"Circuit breaker status: {self.circuit_breaker.state.value}"
       
       def check_connection_health(self):
           """Check connection health."""
           # Simulate connection health check
           health_score = random.uniform(0.8, 1.0)
           if health_score < 0.9:
               return f"WARNING: Connection health low {health_score:.2f}"
           return f"Connection health good: {health_score:.2f}"
       
       def check_performance_metrics(self):
           """Check performance metrics."""
           # Simulate performance metrics
           avg_response_time = random.uniform(100, 500)
           if avg_response_time > 300:
               return f"WARNING: High response time {avg_response_time:.0f}ms"
           return f"Performance good: {avg_response_time:.0f}ms avg"
       
       def demonstrate_fallback_strategies(self):
           """
           Demonstrate fallback strategies.
           """
           logger.info("--- Fallback Strategies ---")
           
           try:
               # Test fallback strategies
               fallback_scenarios = [
                   ("Primary service", self.primary_service_with_fallback),
                   ("Secondary service", self.secondary_service_with_fallback),
                   ("Cache fallback", self.cache_fallback),
                   ("Default response", self.default_response_fallback)
               ]
               
               for scenario_name, scenario in fallback_scenarios:
                   try:
                       logger.info(f"  Testing {scenario_name}...")
                       result = scenario()
                       logger.info(f"    ✓ {scenario_name}: {result}")
                   except Exception as e:
                       logger.info(f"    ❌ {scenario_name}: {e}")
               
               logger.info("✓ Fallback strategies completed")
               
           except Exception as e:
               logger.error(f"Failed fallback strategies: {e}")
       
       def primary_service_with_fallback(self):
           """Primary service with fallback."""
           try:
               # Simulate primary service (may fail)
               if random.random() < 0.4:
                   raise IMAPConnectionError("Primary service unavailable")
               return "Primary service response"
           except Exception as e:
               logger.info(f"    Primary service failed: {e}")
               return self.fallback_service()
       
       def secondary_service_with_fallback(self):
           """Secondary service with fallback."""
           try:
               # Simulate secondary service (may fail)
               if random.random() < 0.2:
                   raise IMAPOperationError("Secondary service unavailable")
               return "Secondary service response"
           except Exception as e:
               logger.info(f"    Secondary service failed: {e}")
               return self.fallback_service()
       
       def cache_fallback(self):
           """Cache fallback strategy."""
           try:
               # Simulate cache access
               return "Cached response"
           except Exception as e:
               logger.info(f"    Cache failed: {e}")
               return "Default cached response"
       
       def default_response_fallback(self):
           """Default response fallback."""
           return "Default fallback response"
       
       def fallback_service(self):
           """Fallback service implementation."""
           return "Fallback service response"
       
       def generate_error_report(self):
           """
           Generate comprehensive error report.
           """
           logger.info("--- Error Report ---")
           
           try:
               report = {
                   'timestamp': datetime.now().isoformat(),
                   'total_errors': self.error_stats['total_errors'],
                   'error_types': self.error_stats['error_types'],
                   'retry_counts': self.error_stats['retry_counts'],
                   'circuit_breaker_trips': self.error_stats['circuit_breaker_trips'],
                   'circuit_breaker_state': self.circuit_breaker.state.value,
                   'failure_count': self.circuit_breaker.failure_count
               }
               
               logger.info("📊 Error Handling Report:")
               logger.info("=" * 50)
               logger.info(f"Total Errors: {report['total_errors']}")
               
               if report['error_types']:
                   logger.info("Error Types:")
                   for error_type, count in report['error_types'].items():
                       logger.info(f"  • {error_type}: {count}")
               
               if report['retry_counts']:
                   logger.info("Retry Counts:")
                   for operation, count in report['retry_counts'].items():
                       logger.info(f"  • {operation}: {count}")
               
               logger.info(f"Circuit Breaker Trips: {report['circuit_breaker_trips']}")
               logger.info(f"Circuit Breaker State: {report['circuit_breaker_state']}")
               logger.info(f"Current Failure Count: {report['failure_count']}")
               logger.info("=" * 50)
               
           except Exception as e:
               logger.error(f"Failed to generate error report: {e}")


   def error_handler(func):
       """
       Decorator for error handling.
       """
       @wraps(func)
       def wrapper(*args, **kwargs):
           try:
               return func(*args, **kwargs)
           except IMAPConnectionError as e:
               logger.error(f"Connection error in {func.__name__}: {e}")
               raise
           except IMAPAuthenticationError as e:
               logger.error(f"Authentication error in {func.__name__}: {e}")
               raise
           except IMAPTimeoutError as e:
               logger.error(f"Timeout error in {func.__name__}: {e}")
               raise
           except IMAPOperationError as e:
               logger.error(f"Operation error in {func.__name__}: {e}")
               raise
           except Exception as e:
               logger.error(f"Unexpected error in {func.__name__}: {e}")
               raise
       return wrapper


   def main():
       """
       Main function to run the error handling example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = ErrorHandlingExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_error_handling()
           logger.info("🎉 Error handling strategies example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Error Classification
--------------------

Exception Types
~~~~~~~~~~~~~~~

.. code-block:: python

   # IMAP-specific exceptions
   try:
       # IMAP operation
       pass
   except IMAPConnectionError as e:
       # Handle connection issues
       logger.error(f"Connection failed: {e}")
   except IMAPAuthenticationError as e:
       # Handle authentication issues
       logger.error(f"Authentication failed: {e}")
   except IMAPTimeoutError as e:
       # Handle timeout issues
       logger.error(f"Operation timed out: {e}")
   except IMAPOperationError as e:
       # Handle operation issues
       logger.error(f"Operation failed: {e}")

Error Categories
~~~~~~~~~~~~~~~~

.. code-block:: python

   def classify_error(exception):
       """Classify errors for appropriate handling."""
       if isinstance(exception, IMAPConnectionError):
           return "CONNECTION"  # Retry with backoff
       elif isinstance(exception, IMAPAuthenticationError):
           return "AUTHENTICATION"  # Don't retry
       elif isinstance(exception, IMAPTimeoutError):
           return "TIMEOUT"  # Retry with timeout adjustment
       elif isinstance(exception, IMAPOperationError):
           return "OPERATION"  # Retry with different parameters
       else:
           return "UNKNOWN"  # Log and escalate

Retry Strategies
----------------

Exponential Backoff
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def exponential_backoff_retry(func, max_attempts=3, base_delay=1.0):
       """Retry with exponential backoff."""
       for attempt in range(max_attempts):
           try:
               return func()
           except Exception as e:
               if attempt == max_attempts - 1:
                   raise
               
               delay = base_delay * (2 ** attempt)
               logger.info(f"Attempt {attempt + 1} failed, retrying in {delay}s")
               time.sleep(delay)

Conditional Retry
~~~~~~~~~~~~~~~~~

.. code-block:: python

   def should_retry(exception, attempt):
       """Determine if operation should be retried."""
       # Don't retry authentication errors
       if isinstance(exception, IMAPAuthenticationError):
           return False
       
       # Don't retry after max attempts
       if attempt >= 3:
           return False
       
       # Retry connection and timeout errors
       if isinstance(exception, (IMAPConnectionError, IMAPTimeoutError)):
           return True
       
       return False

Circuit Breaker
---------------

Implementation
~~~~~~~~~~~~~~

.. code-block:: python

   class CircuitBreaker:
       def __init__(self, failure_threshold=5, recovery_timeout=60):
           self.failure_threshold = failure_threshold
           self.recovery_timeout = recovery_timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
       
       def call(self, func, *args, **kwargs):
           if self.state == "OPEN":
               if self._should_attempt_reset():
                   self.state = "HALF_OPEN"
               else:
                   raise Exception("Circuit breaker is OPEN")
           
           try:
               result = func(*args, **kwargs)
               self._on_success()
               return result
           except Exception as e:
               self._on_failure()
               raise

Usage
~~~~~

.. code-block:: python

   circuit_breaker = CircuitBreaker()
   
   try:
       result = circuit_breaker.call(risky_operation)
   except Exception as e:
       logger.error(f"Operation failed: {e}")

Graceful Degradation
--------------------

Service Levels
~~~~~~~~~~~~~~

.. code-block:: python

   def get_messages_with_degradation():
       """Get messages with graceful degradation."""
       try:
           # Full service - real-time IMAP
           return get_messages_from_imap()
       except IMAPConnectionError:
           try:
               # Degraded service - cached data
               return get_messages_from_cache()
           except Exception:
               # Minimal service - default response
               return get_default_message_response()

Fallback Strategies
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def primary_with_fallback():
       """Primary service with fallback."""
       try:
           return primary_service()
       except Exception as e:
           logger.warning(f"Primary service failed: {e}")
           return fallback_service()

Error Monitoring
----------------

Metrics Collection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ErrorMetrics:
       def __init__(self):
           self.error_counts = {}
           self.error_rates = {}
       
       def record_error(self, error_type, operation):
           key = f"{operation}_{error_type}"
           self.error_counts[key] = self.error_counts.get(key, 0) + 1
       
       def get_error_rate(self, operation):
           # Calculate error rate for operation
           pass

Alerting
~~~~~~~~

.. code-block:: python

   def check_error_thresholds():
       """Check error thresholds and alert."""
       error_rate = get_current_error_rate()
       
       if error_rate > 0.1:  # 10% error rate
           send_alert("High error rate detected")
       
       if circuit_breaker.state == "OPEN":
           send_alert("Circuit breaker is OPEN")

Best Practices
--------------

✅ **DO:**

- Classify errors appropriately

- Implement retry logic with exponential backoff

- Use circuit breakers for external dependencies

- Implement graceful degradation

- Monitor error rates and patterns

- Log errors with context

- Use timeouts for all operations

- Implement fallback strategies

❌ **DON'T:**

- Retry authentication errors

- Use infinite retry loops

- Ignore error patterns

- Skip error logging

- Use fixed retry delays

- Retry permanent errors

- Ignore circuit breaker state

- Skip error monitoring

Error Handling Patterns
-----------------------

Decorator Pattern
~~~~~~~~~~~~~~~~~

.. code-block:: python

   @error_handler
   @retry(max_attempts=3)
   def imap_operation():
       # IMAP operation that may fail
       pass

Context Manager Pattern
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   class ErrorContext:
       def __enter__(self):
           return self
       
       def __exit__(self, exc_type, exc_val, exc_tb):
           if exc_type:
               self.handle_error(exc_type, exc_val, exc_tb)
           return False

Builder Pattern
~~~~~~~~~~~~~~~

.. code-block:: python

   error_handler = (ErrorHandlerBuilder()
                   .with_retry(max_attempts=3)
                   .with_circuit_breaker(threshold=5)
                   .with_fallback(fallback_func)
                   .build())

Next Steps
----------

For more advanced patterns, see:

- :doc:`production_patterns` - Production-ready patterns
- :doc:`monitoring_analytics` - Monitoring and analytics
- :doc:`client_advanced` - Advanced client features
- :doc:`large_volume_handling` - High-performance processing 