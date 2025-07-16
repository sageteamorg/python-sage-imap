#!/usr/bin/env python3
"""
Advanced IMAPClient Features Example

This example demonstrates advanced features and integration patterns of the enhanced
IMAPClient including custom decorators, advanced configurations, integration with
other services, and production-ready patterns.

Author: Python Sage IMAP Library
License: MIT
"""

import logging
import time
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from functools import wraps
import json

from sage_imap.services.client import (
    IMAPClient, 
    ConnectionConfig, 
    ConnectionMetrics,
    retry_on_failure,
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


@dataclass
class ClientConfiguration:
    """Advanced client configuration with environment-specific settings."""
    environment: str
    host: str
    username: str
    password: str
    port: int = 993
    use_ssl: bool = True
    use_pool: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    health_check_interval: float = 60.0
    enable_monitoring: bool = True
    enable_debug: bool = False
    
    @classmethod
    def for_production(cls, host: str, username: str, password: str) -> 'ClientConfiguration':
        """Create production configuration."""
        return cls(
            environment="production",
            host=host,
            username=username,
            password=password,
            max_retries=5,
            retry_delay=2.0,
            timeout=45.0,
            health_check_interval=30.0,
            enable_monitoring=True,
            enable_debug=False
        )
    
    @classmethod
    def for_development(cls, host: str, username: str, password: str) -> 'ClientConfiguration':
        """Create development configuration."""
        return cls(
            environment="development",
            host=host,
            username=username,
            password=password,
            max_retries=2,
            retry_delay=0.5,
            timeout=15.0,
            health_check_interval=10.0,
            enable_monitoring=True,
            enable_debug=True
        )
    
    def to_connection_config(self) -> ConnectionConfig:
        """Convert to ConnectionConfig."""
        return ConnectionConfig(
            host=self.host,
            username=self.username,
            password=self.password,
            port=self.port,
            use_ssl=self.use_ssl,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            timeout=self.timeout,
            health_check_interval=self.health_check_interval,
            enable_monitoring=self.enable_monitoring
        )


class IMAPClientManager:
    """Advanced client manager with lifecycle management and monitoring."""
    
    def __init__(self, config: ClientConfiguration):
        self.config = config
        self.client: Optional[IMAPClient] = None
        self.metrics_history: List[Dict[str, Any]] = []
        self.last_health_check = datetime.now()
        self.health_check_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
    
    def connect(self) -> IMAPClient:
        """Connect with advanced configuration."""
        if self.client and self.client.is_connected():
            return self.client
        
        connection_config = self.config.to_connection_config()
        self.client = IMAPClient.from_config(connection_config, use_pool=self.config.use_pool)
        
        # Configure debug logging if enabled
        if self.config.enable_debug:
            logging.getLogger('sage_imap').setLevel(logging.DEBUG)
        
        self.client.connect()
        
        # Start health monitoring if enabled
        if self.config.enable_monitoring:
            self._start_health_monitoring()
        
        logger.info(f"Connected to {self.config.host} in {self.config.environment} mode")
        return self.client
    
    def disconnect(self):
        """Disconnect with cleanup."""
        self.stop_monitoring.set()
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=2.0)
        
        if self.client:
            self.client.disconnect()
            self.client = None
        
        logger.info("Disconnected from IMAP server")
    
    def get_client(self) -> IMAPClient:
        """Get client with automatic reconnection."""
        if not self.client or not self.client.is_connected():
            self.connect()
        return self.client
    
    def _start_health_monitoring(self):
        """Start background health monitoring."""
        self.stop_monitoring.clear()
        self.health_check_thread = threading.Thread(
            target=self._health_monitoring_loop,
            daemon=True
        )
        self.health_check_thread.start()
    
    def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while not self.stop_monitoring.wait(self.config.health_check_interval):
            if self.client:
                try:
                    health = self.client.health_check()
                    metrics = self.client.get_metrics()
                    
                    # Store metrics history
                    self.metrics_history.append({
                        "timestamp": datetime.now(),
                        "health": health,
                        "metrics": metrics
                    })
                    
                    # Keep only last 100 entries
                    if len(self.metrics_history) > 100:
                        self.metrics_history.pop(0)
                    
                    # Check for issues
                    if not health["is_connected"]:
                        logger.warning("Health check failed - connection lost")
                        try:
                            self.client.connect()
                            logger.info("Connection restored by health monitor")
                        except Exception as e:
                            logger.error(f"Failed to restore connection: {e}")
                    
                    self.last_health_check = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        if not self.client:
            return {}
        
        current_metrics = self.client.get_metrics()
        current_health = self.client.health_check()
        
        summary = {
            "current": {
                "metrics": current_metrics,
                "health": current_health,
                "timestamp": datetime.now()
            },
            "history_count": len(self.metrics_history),
            "last_health_check": self.last_health_check,
            "configuration": {
                "environment": self.config.environment,
                "host": self.config.host,
                "monitoring_enabled": self.config.enable_monitoring,
                "pool_enabled": self.config.use_pool
            }
        }
        
        # Add trend analysis if we have history
        if len(self.metrics_history) >= 2:
            first = self.metrics_history[0]
            last = self.metrics_history[-1]
            
            summary["trends"] = {
                "operations_growth": last["metrics"].total_operations - first["metrics"].total_operations,
                "success_rate_change": last["health"]["success_rate"] - first["health"]["success_rate"],
                "response_time_change": last["metrics"].average_response_time - first["metrics"].average_response_time
            }
        
        return summary


def operation_timing_decorator(operation_name: str):
    """Decorator to time and log operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(f"Operation '{operation_name}' completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Operation '{operation_name}' failed after {execution_time:.3f}s: {e}")
                raise
        return wrapper
    return decorator


def advanced_configuration_example():
    """
    Demonstrates advanced configuration patterns.
    
    This example shows:
    - Environment-specific configurations
    - Advanced client management
    - Configuration validation
    - Production-ready patterns
    """
    print("=" * 60)
    print("ADVANCED CONFIGURATION EXAMPLE")
    print("=" * 60)
    
    # Test different environment configurations
    environments = [
        ClientConfiguration.for_development(
            host="imap.gmail.com",
            username="your_email@gmail.com",
            password="your_password"
        ),
        ClientConfiguration.for_production(
            host="imap.gmail.com",
            username="your_email@gmail.com",
            password="your_password"
        )
    ]
    
    for config in environments:
        print(f"\nTesting {config.environment} configuration:")
        print(f"  - Max retries: {config.max_retries}")
        print(f"  - Retry delay: {config.retry_delay}s")
        print(f"  - Timeout: {config.timeout}s")
        print(f"  - Health check interval: {config.health_check_interval}s")
        print(f"  - Monitoring enabled: {config.enable_monitoring}")
        print(f"  - Debug enabled: {config.enable_debug}")
        
        try:
            with IMAPClientManager(config) as manager:
                client = manager.get_client()
                
                # Perform test operations
                status, data = client.select("INBOX")
                print(f"  ✓ Connected and selected INBOX ({data[0]} messages)")
                
                # Show metrics
                summary = manager.get_metrics_summary()
                current = summary["current"]
                print(f"  - Operations: {current['metrics'].total_operations}")
                print(f"  - Success rate: {current['health']['success_rate']:.1f}%")
                print(f"  - Response time: {current['metrics'].average_response_time:.3f}s")
                
        except Exception as e:
            print(f"  ✗ {config.environment} configuration failed: {e}")


def custom_decorators_example():
    """
    Demonstrates custom decorators for IMAP operations.
    
    This example shows:
    - Custom operation decorators
    - Timing and logging decorators
    - Error handling decorators
    - Performance monitoring decorators
    """
    print("\n" + "=" * 60)
    print("CUSTOM DECORATORS EXAMPLE")
    print("=" * 60)
    
    config = ClientConfiguration.for_development(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password"
    )
    
    # Define custom operations with decorators
    @operation_timing_decorator("list_mailboxes")
    @retry_on_failure(max_retries=2, delay=1.0)
    def list_mailboxes(client: IMAPClient) -> List[str]:
        """List all mailboxes with timing and retry."""
        status, mailboxes = client.list()
        if status != "OK":
            raise Exception(f"Failed to list mailboxes: {status}")
        return [mb.decode() for mb in mailboxes]
    
    @operation_timing_decorator("get_inbox_count")
    @retry_on_failure(max_retries=3, delay=0.5)
    def get_inbox_count(client: IMAPClient) -> int:
        """Get INBOX message count with timing and retry."""
        status, data = client.select("INBOX")
        if status != "OK":
            raise Exception(f"Failed to select INBOX: {status}")
        return int(data[0])
    
    @operation_timing_decorator("server_capabilities")
    def get_server_capabilities(client: IMAPClient) -> List[str]:
        """Get server capabilities with timing."""
        return list(client.capabilities)
    
    try:
        with IMAPClientManager(config) as manager:
            client = manager.get_client()
            
            print("Executing decorated operations:")
            
            # Execute operations with decorators
            mailboxes = list_mailboxes(client)
            print(f"  ✓ Found {len(mailboxes)} mailboxes")
            
            inbox_count = get_inbox_count(client)
            print(f"  ✓ INBOX has {inbox_count} messages")
            
            capabilities = get_server_capabilities(client)
            print(f"  ✓ Server has {len(capabilities)} capabilities")
            
            # Show operation metrics
            summary = manager.get_metrics_summary()
            print(f"\nOperation Metrics:")
            print(f"  - Total operations: {summary['current']['metrics'].total_operations}")
            print(f"  - Average response time: {summary['current']['metrics'].average_response_time:.3f}s")
            
    except Exception as e:
        print(f"✗ Custom decorators example failed: {e}")


def connection_lifecycle_example():
    """
    Demonstrates advanced connection lifecycle management.
    
    This example shows:
    - Connection lifecycle hooks
    - Automatic reconnection
    - Resource cleanup
    - State management
    """
    print("\n" + "=" * 60)
    print("CONNECTION LIFECYCLE EXAMPLE")
    print("=" * 60)
    
    config = ClientConfiguration.for_development(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password"
    )
    
    class LifecycleAwareClient:
        """Client wrapper with lifecycle hooks."""
        
        def __init__(self, manager: IMAPClientManager):
            self.manager = manager
            self.operation_count = 0
            self.connection_events = []
        
        def on_connect(self):
            """Called when connection is established."""
            self.connection_events.append(("connect", datetime.now()))
            logger.info("Connection established")
        
        def on_disconnect(self):
            """Called when connection is closed."""
            self.connection_events.append(("disconnect", datetime.now()))
            logger.info("Connection closed")
        
        def on_operation(self, operation_name: str):
            """Called before each operation."""
            self.operation_count += 1
            logger.debug(f"Executing operation {self.operation_count}: {operation_name}")
        
        @contextmanager
        def operation_context(self, operation_name: str):
            """Context manager for operations."""
            self.on_operation(operation_name)
            start_time = time.time()
            try:
                yield
                execution_time = time.time() - start_time
                logger.info(f"Operation '{operation_name}' completed in {execution_time:.3f}s")
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Operation '{operation_name}' failed after {execution_time:.3f}s: {e}")
                raise
        
        def get_lifecycle_summary(self) -> Dict[str, Any]:
            """Get lifecycle summary."""
            return {
                "operation_count": self.operation_count,
                "connection_events": self.connection_events,
                "uptime": (datetime.now() - self.connection_events[0][1]).total_seconds() if self.connection_events else 0
            }
    
    try:
        with IMAPClientManager(config) as manager:
            lifecycle_client = LifecycleAwareClient(manager)
            lifecycle_client.on_connect()
            
            client = manager.get_client()
            
            # Perform operations with lifecycle tracking
            operations = [
                ("list_mailboxes", lambda: client.list()),
                ("select_inbox", lambda: client.select("INBOX")),
                ("get_capabilities", lambda: client.capability()),
                ("server_noop", lambda: client.noop()),
            ]
            
            for op_name, operation in operations:
                with lifecycle_client.operation_context(op_name):
                    result = operation()
                    print(f"  ✓ {op_name} completed")
            
            # Show lifecycle summary
            lifecycle_client.on_disconnect()
            summary = lifecycle_client.get_lifecycle_summary()
            
            print(f"\nLifecycle Summary:")
            print(f"  - Total operations: {summary['operation_count']}")
            print(f"  - Connection events: {len(summary['connection_events'])}")
            print(f"  - Session uptime: {summary['uptime']:.1f}s")
            
            for event_type, timestamp in summary['connection_events']:
                print(f"  - {event_type}: {timestamp.strftime('%H:%M:%S')}")
            
    except Exception as e:
        print(f"✗ Connection lifecycle example failed: {e}")


def integration_patterns_example():
    """
    Demonstrates integration patterns with other systems.
    
    This example shows:
    - Integration with logging systems
    - Metrics export for monitoring
    - Event-driven patterns
    - Service integration
    """
    print("\n" + "=" * 60)
    print("INTEGRATION PATTERNS EXAMPLE")
    print("=" * 60)
    
    class MetricsExporter:
        """Export metrics to external systems."""
        
        def __init__(self):
            self.exported_metrics = []
        
        def export_to_prometheus(self, metrics: ConnectionMetrics) -> str:
            """Export metrics in Prometheus format."""
            prometheus_metrics = [
                f"imap_connection_attempts_total {metrics.connection_attempts}",
                f"imap_successful_connections_total {metrics.successful_connections}",
                f"imap_failed_connections_total {metrics.failed_connections}",
                f"imap_operations_total {metrics.total_operations}",
                f"imap_failed_operations_total {metrics.failed_operations}",
                f"imap_average_response_time_seconds {metrics.average_response_time}",
                f"imap_connection_uptime_seconds {metrics.connection_uptime.total_seconds()}"
            ]
            return "\n".join(prometheus_metrics)
        
        def export_to_json(self, metrics: ConnectionMetrics, health: Dict[str, Any]) -> str:
            """Export metrics in JSON format."""
            from dataclasses import asdict
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics),
                "health": health
            }
            return json.dumps(export_data, indent=2, default=str)
        
        def send_to_monitoring_system(self, data: str, format_type: str):
            """Simulate sending to monitoring system."""
            self.exported_metrics.append({
                "timestamp": datetime.now(),
                "format": format_type,
                "data": data
            })
            print(f"  ✓ Exported metrics in {format_type} format")
    
    class EventHandler:
        """Handle IMAP events."""
        
        def __init__(self):
            self.events = []
        
        def on_connection_established(self, host: str):
            """Handle connection established event."""
            event = {
                "type": "connection_established",
                "host": host,
                "timestamp": datetime.now()
            }
            self.events.append(event)
            logger.info(f"Event: Connection established to {host}")
        
        def on_operation_completed(self, operation: str, duration: float):
            """Handle operation completed event."""
            event = {
                "type": "operation_completed",
                "operation": operation,
                "duration": duration,
                "timestamp": datetime.now()
            }
            self.events.append(event)
            logger.debug(f"Event: Operation '{operation}' completed in {duration:.3f}s")
        
        def on_error_occurred(self, error: str, operation: str = None):
            """Handle error event."""
            event = {
                "type": "error_occurred",
                "error": error,
                "operation": operation,
                "timestamp": datetime.now()
            }
            self.events.append(event)
            logger.error(f"Event: Error in {operation or 'unknown'}: {error}")
        
        def get_event_summary(self) -> Dict[str, Any]:
            """Get event summary."""
            event_counts = {}
            for event in self.events:
                event_type = event["type"]
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            return {
                "total_events": len(self.events),
                "event_counts": event_counts,
                "recent_events": self.events[-5:] if self.events else []
            }
    
    # Initialize integration components
    metrics_exporter = MetricsExporter()
    event_handler = EventHandler()
    
    config = ClientConfiguration.for_development(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password"
    )
    
    try:
        with IMAPClientManager(config) as manager:
            client = manager.get_client()
            event_handler.on_connection_established(config.host)
            
            # Perform operations with event handling
            operations = [
                ("list", lambda: client.list()),
                ("select", lambda: client.select("INBOX")),
                ("noop", lambda: client.noop()),
            ]
            
            for op_name, operation in operations:
                try:
                    start_time = time.time()
                    result = operation()
                    duration = time.time() - start_time
                    
                    event_handler.on_operation_completed(op_name, duration)
                    print(f"  ✓ {op_name} completed in {duration:.3f}s")
                    
                except Exception as e:
                    event_handler.on_error_occurred(str(e), op_name)
                    print(f"  ✗ {op_name} failed: {e}")
            
            # Export metrics
            print(f"\nExporting metrics to external systems:")
            
            metrics = client.get_metrics()
            health = client.health_check()
            
            # Export to different formats
            prometheus_data = metrics_exporter.export_to_prometheus(metrics)
            json_data = metrics_exporter.export_to_json(metrics, health)
            
            metrics_exporter.send_to_monitoring_system(prometheus_data, "prometheus")
            metrics_exporter.send_to_monitoring_system(json_data, "json")
            
            # Show integration summary
            print(f"\nIntegration Summary:")
            event_summary = event_handler.get_event_summary()
            print(f"  - Total events: {event_summary['total_events']}")
            print(f"  - Event types: {list(event_summary['event_counts'].keys())}")
            print(f"  - Metrics exports: {len(metrics_exporter.exported_metrics)}")
            
            # Show recent events
            print(f"\nRecent Events:")
            for event in event_summary['recent_events']:
                print(f"  - {event['type']}: {event.get('operation', 'N/A')} at {event['timestamp'].strftime('%H:%M:%S')}")
            
    except Exception as e:
        print(f"✗ Integration patterns example failed: {e}")


def production_ready_patterns():
    """
    Demonstrates production-ready patterns and best practices.
    
    This example shows:
    - Production configuration
    - Error handling strategies
    - Monitoring and alerting
    - Performance optimization
    """
    print("\n" + "=" * 60)
    print("PRODUCTION-READY PATTERNS EXAMPLE")
    print("=" * 60)
    
    class ProductionIMAPService:
        """Production-ready IMAP service."""
        
        def __init__(self, config: ClientConfiguration):
            self.config = config
            self.manager = IMAPClientManager(config)
            self.circuit_breaker_failures = 0
            self.circuit_breaker_threshold = 5
            self.circuit_breaker_timeout = 60  # seconds
            self.last_failure_time = None
        
        def is_circuit_breaker_open(self) -> bool:
            """Check if circuit breaker is open."""
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                if self.last_failure_time:
                    time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                    return time_since_failure < self.circuit_breaker_timeout
            return False
        
        def execute_with_circuit_breaker(self, operation: Callable, operation_name: str):
            """Execute operation with circuit breaker pattern."""
            if self.is_circuit_breaker_open():
                raise Exception(f"Circuit breaker open for {operation_name}")
            
            try:
                result = operation()
                # Reset circuit breaker on success
                self.circuit_breaker_failures = 0
                self.last_failure_time = None
                return result
            except Exception as e:
                self.circuit_breaker_failures += 1
                self.last_failure_time = datetime.now()
                logger.error(f"Circuit breaker failure {self.circuit_breaker_failures}/{self.circuit_breaker_threshold} for {operation_name}: {e}")
                raise
        
        def get_health_status(self) -> Dict[str, Any]:
            """Get comprehensive health status."""
            try:
                client = self.manager.get_client()
                health = client.health_check()
                metrics = client.get_metrics()
                
                return {
                    "status": "healthy" if health["is_connected"] else "unhealthy",
                    "connection": health["is_connected"],
                    "success_rate": health["success_rate"],
                    "response_time": metrics.average_response_time,
                    "circuit_breaker": {
                        "failures": self.circuit_breaker_failures,
                        "is_open": self.is_circuit_breaker_open()
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    # Test production patterns
    config = ClientConfiguration.for_production(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password"
    )
    
    service = ProductionIMAPService(config)
    
    try:
        print("Testing production-ready patterns:")
        
        # Test normal operations
        with service.manager:
            client = service.manager.get_client()
            
            # Test operations with circuit breaker
            operations = [
                ("list_mailboxes", lambda: client.list()),
                ("select_inbox", lambda: client.select("INBOX")),
                ("get_capabilities", lambda: client.capability()),
            ]
            
            for op_name, operation in operations:
                try:
                    result = service.execute_with_circuit_breaker(operation, op_name)
                    print(f"  ✓ {op_name} completed successfully")
                except Exception as e:
                    print(f"  ✗ {op_name} failed: {e}")
            
            # Show health status
            health_status = service.get_health_status()
            print(f"\nHealth Status:")
            print(f"  - Status: {health_status['status']}")
            print(f"  - Connected: {health_status['connection']}")
            print(f"  - Success rate: {health_status['success_rate']:.1f}%")
            print(f"  - Response time: {health_status['response_time']:.3f}s")
            print(f"  - Circuit breaker failures: {health_status['circuit_breaker']['failures']}")
            print(f"  - Circuit breaker open: {health_status['circuit_breaker']['is_open']}")
            
            # Show metrics summary
            summary = service.manager.get_metrics_summary()
            print(f"\nProduction Metrics:")
            print(f"  - Environment: {summary['configuration']['environment']}")
            print(f"  - Monitoring enabled: {summary['configuration']['monitoring_enabled']}")
            print(f"  - Pool enabled: {summary['configuration']['pool_enabled']}")
            print(f"  - History entries: {summary['history_count']}")
            
    except Exception as e:
        print(f"✗ Production patterns example failed: {e}")


def main():
    """
    Main function to run all advanced client feature examples.
    
    This function demonstrates comprehensive advanced features including
    configuration management, custom decorators, lifecycle management,
    integration patterns, and production-ready patterns.
    """
    print("Enhanced IMAPClient Advanced Features Examples")
    print("=" * 60)
    print("This script demonstrates advanced features and integration patterns of IMAPClient.")
    print("Note: Update the credentials in each example before running.")
    print()
    
    # Run all examples
    examples = [
        advanced_configuration_example,
        custom_decorators_example,
        connection_lifecycle_example,
        integration_patterns_example,
        production_ready_patterns,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Example {example.__name__} failed: {e}")
        
        # Small delay between examples
        time.sleep(1.0)
    
    # Clean up connection pool
    clear_connection_pool()
    
    print("\n" + "=" * 60)
    print("All advanced client feature examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main() 