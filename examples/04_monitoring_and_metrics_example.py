#!/usr/bin/env python3
"""
Monitoring and Metrics Example

This example demonstrates the comprehensive monitoring and metrics features of the
enhanced IMAPClient including performance tracking, health monitoring, and
statistical analysis.

Author: Python Sage IMAP Library
License: MIT
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import asdict

from sage_imap.services.client import IMAPClient, ConnectionConfig, ConnectionMetrics
from sage_imap.exceptions import IMAPConnectionError, IMAPAuthenticationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Helper class to collect and analyze metrics over time."""
    
    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def capture_snapshot(self, client: IMAPClient, label: str = ""):
        """Capture a metrics snapshot."""
        metrics = client.get_metrics()
        health = client.health_check()
        
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "label": label,
            "metrics": asdict(metrics),
            "health": health,
            "uptime": (datetime.now() - self.start_time).total_seconds()
        }
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics from all snapshots."""
        if not self.snapshots:
            return {}
        
        total_ops = [s["metrics"]["total_operations"] for s in self.snapshots]
        response_times = [s["metrics"]["average_response_time"] for s in self.snapshots]
        success_rates = [s["health"]["success_rate"] for s in self.snapshots]
        
        return {
            "total_snapshots": len(self.snapshots),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "operations": {
                "total": max(total_ops) if total_ops else 0,
                "rate": max(total_ops) / ((datetime.now() - self.start_time).total_seconds()) if total_ops else 0
            },
            "performance": {
                "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0
            },
            "reliability": {
                "avg_success_rate": sum(success_rates) / len(success_rates) if success_rates else 0,
                "min_success_rate": min(success_rates) if success_rates else 0,
                "max_success_rate": max(success_rates) if success_rates else 0
            }
        }


def basic_metrics_example():
    """
    Demonstrates basic metrics collection and analysis.
    
    This example shows:
    - Basic metrics collection
    - Metrics interpretation
    - Performance tracking
    - Connection statistics
    """
    print("=" * 60)
    print("BASIC METRICS EXAMPLE")
    print("=" * 60)
    
    # Configuration
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        enable_monitoring=True,
        max_retries=3,
        retry_delay=1.0
    )
    
    client = IMAPClient.from_config(config)
    collector = MetricsCollector()
    
    try:
        print("Starting basic metrics collection...")
        
        # Initial connection
        client.connect()
        collector.capture_snapshot(client, "Initial connection")
        
        # Perform various operations
        operations = [
            ("List mailboxes", lambda: client.list()),
            ("Select INBOX", lambda: client.select("INBOX")),
            ("Get capabilities", lambda: client.capability()),
            ("Server noop", lambda: client.noop()),
            ("Status check", lambda: client.status("INBOX", "(MESSAGES RECENT)")),
        ]
        
        for op_name, operation in operations:
            print(f"\nPerforming: {op_name}")
            
            start_time = time.time()
            try:
                result = operation()
                execution_time = time.time() - start_time
                print(f"  ✓ Completed in {execution_time:.3f}s")
                
                # Capture metrics after each operation
                snapshot = collector.capture_snapshot(client, f"After {op_name}")
                print(f"  - Total operations: {snapshot['metrics']['total_operations']}")
                print(f"  - Average response time: {snapshot['metrics']['average_response_time']:.3f}s")
                print(f"  - Success rate: {snapshot['health']['success_rate']:.1f}%")
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"  ✗ Failed in {execution_time:.3f}s: {e}")
                collector.capture_snapshot(client, f"Failed {op_name}")
        
        # Final metrics summary
        print("\n" + "=" * 40)
        print("FINAL METRICS SUMMARY")
        print("=" * 40)
        
        final_metrics = client.get_metrics()
        print(f"Connection Statistics:")
        print(f"  - Total connection attempts: {final_metrics.connection_attempts}")
        print(f"  - Successful connections: {final_metrics.successful_connections}")
        print(f"  - Failed connections: {final_metrics.failed_connections}")
        print(f"  - Reconnection attempts: {final_metrics.reconnection_attempts}")
        
        print(f"\nOperation Statistics:")
        print(f"  - Total operations: {final_metrics.total_operations}")
        print(f"  - Failed operations: {final_metrics.failed_operations}")
        print(f"  - Success rate: {((final_metrics.total_operations - final_metrics.failed_operations) / final_metrics.total_operations * 100):.1f}%")
        print(f"  - Average response time: {final_metrics.average_response_time:.3f}s")
        
        print(f"\nConnection Health:")
        print(f"  - Last connection: {final_metrics.last_connection_time}")
        print(f"  - Connection uptime: {final_metrics.connection_uptime}")
        print(f"  - Last error: {final_metrics.last_error}")
        
    except Exception as e:
        print(f"✗ Basic metrics example failed: {e}")
    finally:
        client.disconnect()
        
        # Show collector summary
        summary = collector.get_summary()
        print(f"\nCollector Summary:")
        print(f"  - Total snapshots: {summary.get('total_snapshots', 0)}")
        print(f"  - Duration: {summary.get('duration', 0):.1f}s")
        if 'operations' in summary:
            print(f"  - Operation rate: {summary['operations']['rate']:.2f} ops/sec")


def performance_monitoring_example():
    """
    Demonstrates performance monitoring and analysis.
    
    This example shows:
    - Performance tracking over time
    - Response time analysis
    - Throughput measurement
    - Performance optimization insights
    """
    print("\n" + "=" * 60)
    print("PERFORMANCE MONITORING EXAMPLE")
    print("=" * 60)
    
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        enable_monitoring=True,
        timeout=30.0
    )
    
    client = IMAPClient.from_config(config)
    collector = MetricsCollector()
    
    try:
        print("Starting performance monitoring...")
        
        client.connect()
        collector.capture_snapshot(client, "Connected")
        
        # Perform operations with timing
        num_operations = 10
        operation_times = []
        
        print(f"Performing {num_operations} operations for performance analysis...")
        
        for i in range(num_operations):
            start_time = time.time()
            
            try:
                # Alternate between operations
                if i % 3 == 0:
                    client.noop()
                    op_type = "noop"
                elif i % 3 == 1:
                    client.list()
                    op_type = "list"
                else:
                    client.select("INBOX")
                    op_type = "select"
                
                execution_time = time.time() - start_time
                operation_times.append({
                    "operation": op_type,
                    "time": execution_time,
                    "timestamp": datetime.now()
                })
                
                if i % 2 == 0:
                    collector.capture_snapshot(client, f"Operation {i+1}")
                
                print(f"  Operation {i+1} ({op_type}): {execution_time:.3f}s")
                
            except Exception as e:
                execution_time = time.time() - start_time
                print(f"  Operation {i+1} failed: {e} (took {execution_time:.3f}s)")
            
            # Small delay between operations
            time.sleep(0.2)
        
        # Performance analysis
        print("\n" + "=" * 40)
        print("PERFORMANCE ANALYSIS")
        print("=" * 40)
        
        if operation_times:
            times_by_op = {}
            for op_data in operation_times:
                op_type = op_data["operation"]
                if op_type not in times_by_op:
                    times_by_op[op_type] = []
                times_by_op[op_type].append(op_data["time"])
            
            print("Performance by operation type:")
            for op_type, times in times_by_op.items():
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                print(f"  {op_type}:")
                print(f"    - Average: {avg_time:.3f}s")
                print(f"    - Min: {min_time:.3f}s")
                print(f"    - Max: {max_time:.3f}s")
                print(f"    - Count: {len(times)}")
        
        # Overall performance metrics
        final_metrics = client.get_metrics()
        total_time = sum(op["time"] for op in operation_times)
        
        print(f"\nOverall Performance:")
        print(f"  - Total execution time: {total_time:.3f}s")
        print(f"  - Average operation time: {total_time / len(operation_times):.3f}s")
        print(f"  - Operations per second: {len(operation_times) / total_time:.2f}")
        print(f"  - Client average response time: {final_metrics.average_response_time:.3f}s")
        
    except Exception as e:
        print(f"✗ Performance monitoring example failed: {e}")
    finally:
        client.disconnect()


def health_monitoring_example():
    """
    Demonstrates health monitoring and alerting.
    
    This example shows:
    - Continuous health monitoring
    - Health status interpretation
    - Alert conditions
    - Health trend analysis
    """
    print("\n" + "=" * 60)
    print("HEALTH MONITORING EXAMPLE")
    print("=" * 60)
    
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        health_check_interval=2.0,  # Check every 2 seconds
        enable_monitoring=True
    )
    
    client = IMAPClient.from_config(config)
    health_history = []
    
    def check_health_alerts(health_data: Dict[str, Any]) -> List[str]:
        """Check for health alert conditions."""
        alerts = []
        
        if not health_data.get("is_connected", False):
            alerts.append("CRITICAL: Connection lost")
        
        if health_data.get("success_rate", 100) < 90:
            alerts.append(f"WARNING: Low success rate ({health_data['success_rate']:.1f}%)")
        
        if health_data.get("average_response_time", 0) > 5.0:
            alerts.append(f"WARNING: High response time ({health_data['average_response_time']:.3f}s)")
        
        if health_data.get("connection_age", 0) > 300:  # 5 minutes
            alerts.append("INFO: Long-running connection")
        
        return alerts
    
    try:
        print("Starting health monitoring...")
        
        client.connect()
        print("✓ Connected with health monitoring enabled")
        
        # Monitor health over time
        monitoring_duration = 15  # seconds
        check_interval = 2  # seconds
        checks = monitoring_duration // check_interval
        
        print(f"Monitoring health for {monitoring_duration} seconds...")
        
        for i in range(checks):
            print(f"\nHealth check {i+1}/{checks}:")
            
            # Get health status
            health = client.health_check()
            health_history.append({
                "timestamp": datetime.now(),
                "health": health.copy()
            })
            
            # Display health status
            print(f"  - Connected: {health['is_connected']}")
            print(f"  - Connection age: {health['connection_age']:.1f}s")
            print(f"  - Total operations: {health['total_operations']}")
            print(f"  - Success rate: {health['success_rate']:.1f}%")
            print(f"  - Average response time: {health['average_response_time']:.3f}s")
            
            # Check for alerts
            alerts = check_health_alerts(health)
            if alerts:
                print("  ALERTS:")
                for alert in alerts:
                    print(f"    - {alert}")
            else:
                print("  - Status: Healthy")
            
            # Perform some operations to affect metrics
            if i % 2 == 0:
                try:
                    client.noop()
                    print("  - Performed noop operation")
                except Exception as e:
                    print(f"  - Operation failed: {e}")
            
            time.sleep(check_interval)
        
        # Health trend analysis
        print("\n" + "=" * 40)
        print("HEALTH TREND ANALYSIS")
        print("=" * 40)
        
        if len(health_history) >= 2:
            first_check = health_history[0]["health"]
            last_check = health_history[-1]["health"]
            
            print("Health trends:")
            print(f"  - Operations: {first_check['total_operations']} → {last_check['total_operations']}")
            print(f"  - Success rate: {first_check['success_rate']:.1f}% → {last_check['success_rate']:.1f}%")
            print(f"  - Response time: {first_check['average_response_time']:.3f}s → {last_check['average_response_time']:.3f}s")
            
            # Calculate trends
            ops_trend = last_check['total_operations'] - first_check['total_operations']
            success_trend = last_check['success_rate'] - first_check['success_rate']
            time_trend = last_check['average_response_time'] - first_check['average_response_time']
            
            print(f"\nTrend analysis:")
            print(f"  - Operations change: {ops_trend:+d}")
            print(f"  - Success rate change: {success_trend:+.1f}%")
            print(f"  - Response time change: {time_trend:+.3f}s")
        
    except Exception as e:
        print(f"✗ Health monitoring example failed: {e}")
    finally:
        client.disconnect()


def metrics_export_example():
    """
    Demonstrates metrics export and reporting.
    
    This example shows:
    - Metrics data export
    - Report generation
    - Data serialization
    - Integration with monitoring systems
    """
    print("\n" + "=" * 60)
    print("METRICS EXPORT EXAMPLE")
    print("=" * 60)
    
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        enable_monitoring=True
    )
    
    client = IMAPClient.from_config(config)
    collector = MetricsCollector()
    
    try:
        print("Collecting metrics for export...")
        
        client.connect()
        collector.capture_snapshot(client, "Connected")
        
        # Perform operations
        operations = ["list", "select", "noop", "capability"]
        for op in operations:
            try:
                if op == "list":
                    client.list()
                elif op == "select":
                    client.select("INBOX")
                elif op == "noop":
                    client.noop()
                elif op == "capability":
                    client.capability()
                
                collector.capture_snapshot(client, f"After {op}")
                print(f"  ✓ {op} completed")
                
            except Exception as e:
                print(f"  ✗ {op} failed: {e}")
                collector.capture_snapshot(client, f"Failed {op}")
        
        # Export metrics in different formats
        print("\n" + "=" * 40)
        print("METRICS EXPORT")
        print("=" * 40)
        
        # 1. JSON export
        final_metrics = client.get_metrics()
        final_health = client.health_check()
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "client_info": {
                "host": config.host,
                "username": config.username,
                "port": config.port,
                "use_ssl": config.use_ssl
            },
            "metrics": asdict(final_metrics),
            "health": final_health,
            "snapshots": collector.snapshots,
            "summary": collector.get_summary()
        }
        
        # Save to file (example)
        try:
            with open("imap_metrics_export.json", "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            print("✓ Metrics exported to imap_metrics_export.json")
        except Exception as e:
            print(f"✗ Failed to export to file: {e}")
        
        # 2. Console report
        print("\nConsole Report:")
        print("-" * 30)
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Server: {config.host}:{config.port}")
        print(f"Connection uptime: {final_metrics.connection_uptime}")
        print(f"Total operations: {final_metrics.total_operations}")
        print(f"Success rate: {((final_metrics.total_operations - final_metrics.failed_operations) / final_metrics.total_operations * 100):.1f}%")
        print(f"Average response time: {final_metrics.average_response_time:.3f}s")
        
        # 3. Prometheus-style metrics
        print("\nPrometheus-style metrics:")
        print("-" * 30)
        print(f"imap_connection_attempts_total {final_metrics.connection_attempts}")
        print(f"imap_successful_connections_total {final_metrics.successful_connections}")
        print(f"imap_failed_connections_total {final_metrics.failed_connections}")
        print(f"imap_operations_total {final_metrics.total_operations}")
        print(f"imap_failed_operations_total {final_metrics.failed_operations}")
        print(f"imap_average_response_time_seconds {final_metrics.average_response_time}")
        print(f"imap_connection_uptime_seconds {final_metrics.connection_uptime.total_seconds()}")
        
        # 4. Summary statistics
        summary = collector.get_summary()
        print(f"\nSummary Statistics:")
        print("-" * 30)
        if summary:
            print(f"Monitoring duration: {summary['duration']:.1f}s")
            print(f"Snapshots collected: {summary['total_snapshots']}")
            if 'operations' in summary:
                print(f"Operation rate: {summary['operations']['rate']:.2f} ops/sec")
            if 'performance' in summary:
                perf = summary['performance']
                print(f"Response time (avg/min/max): {perf['avg_response_time']:.3f}s / {perf['min_response_time']:.3f}s / {perf['max_response_time']:.3f}s")
        
    except Exception as e:
        print(f"✗ Metrics export example failed: {e}")
    finally:
        client.disconnect()


def real_time_monitoring_example():
    """
    Demonstrates real-time monitoring dashboard simulation.
    
    This example shows:
    - Real-time metrics updates
    - Dashboard-style display
    - Live performance monitoring
    - Alert generation
    """
    print("\n" + "=" * 60)
    print("REAL-TIME MONITORING EXAMPLE")
    print("=" * 60)
    
    config = ConnectionConfig(
        host="imap.gmail.com",
        username="your_email@gmail.com",
        password="your_password",
        enable_monitoring=True,
        health_check_interval=1.0
    )
    
    client = IMAPClient.from_config(config)
    
    def display_dashboard(metrics: ConnectionMetrics, health: Dict[str, Any]):
        """Display a simple dashboard."""
        print("\033[2J\033[H", end="")  # Clear screen
        print("=" * 60)
        print("IMAP CLIENT REAL-TIME DASHBOARD")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Server: {config.host}:{config.port}")
        print()
        
        # Connection status
        status_icon = "🟢" if health["is_connected"] else "🔴"
        print(f"Connection Status: {status_icon} {'CONNECTED' if health['is_connected'] else 'DISCONNECTED'}")
        print(f"Connection Age: {health['connection_age']:.1f}s")
        print()
        
        # Metrics
        print("METRICS:")
        print(f"  Total Operations: {metrics.total_operations}")
        print(f"  Failed Operations: {metrics.failed_operations}")
        print(f"  Success Rate: {health['success_rate']:.1f}%")
        print(f"  Average Response Time: {metrics.average_response_time:.3f}s")
        print(f"  Connection Attempts: {metrics.connection_attempts}")
        print(f"  Reconnections: {metrics.reconnection_attempts}")
        print()
        
        # Health indicators
        print("HEALTH INDICATORS:")
        if health["success_rate"] >= 95:
            print("  ✅ Success Rate: Excellent")
        elif health["success_rate"] >= 90:
            print("  ⚠️  Success Rate: Good")
        else:
            print("  ❌ Success Rate: Poor")
        
        if metrics.average_response_time < 1.0:
            print("  ✅ Response Time: Fast")
        elif metrics.average_response_time < 3.0:
            print("  ⚠️  Response Time: Moderate")
        else:
            print("  ❌ Response Time: Slow")
        
        print()
        print("Press Ctrl+C to stop monitoring...")
    
    try:
        print("Starting real-time monitoring dashboard...")
        print("(This will update every 2 seconds)")
        
        client.connect()
        
        # Real-time monitoring loop
        operation_count = 0
        
        while True:
            # Get current metrics
            metrics = client.get_metrics()
            health = client.health_check()
            
            # Display dashboard
            display_dashboard(metrics, health)
            
            # Perform an operation to generate activity
            try:
                if operation_count % 3 == 0:
                    client.noop()
                elif operation_count % 3 == 1:
                    client.list()
                else:
                    client.select("INBOX")
                
                operation_count += 1
                
            except Exception as e:
                print(f"Operation failed: {e}")
            
            # Wait before next update
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"✗ Real-time monitoring failed: {e}")
    finally:
        client.disconnect()


def main():
    """
    Main function to run all monitoring and metrics examples.
    
    This function demonstrates comprehensive monitoring and metrics features
    including basic metrics, performance monitoring, health monitoring,
    metrics export, and real-time monitoring.
    """
    print("Enhanced IMAPClient Monitoring and Metrics Examples")
    print("=" * 60)
    print("This script demonstrates the monitoring and metrics features of IMAPClient.")
    print("Note: Update the credentials in each example before running.")
    print()
    
    # Run all examples
    examples = [
        basic_metrics_example,
        performance_monitoring_example,
        health_monitoring_example,
        metrics_export_example,
        # real_time_monitoring_example,  # Commented out as it's interactive
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"✗ Example {example.__name__} failed: {e}")
        
        # Small delay between examples
        time.sleep(1.0)
    
    print("\n" + "=" * 60)
    print("All monitoring and metrics examples completed!")
    print("Uncomment real_time_monitoring_example() to try the interactive dashboard.")
    print("=" * 60)


if __name__ == "__main__":
    main() 