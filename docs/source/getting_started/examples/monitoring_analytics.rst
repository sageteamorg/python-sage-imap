.. _monitoring_analytics:

Monitoring and Analytics
========================

This example demonstrates comprehensive monitoring and analytics for IMAP operations including metrics collection, performance tracking, alerting, and operational insights.

**⚠️ IMPORTANT: This example covers enterprise-grade monitoring and analytics!**

Overview
--------

You'll learn how to:

- Collect performance metrics
- Monitor connection health
- Track operational metrics
- Implement alerting systems
- Generate analytics reports
- Create dashboards
- Monitor resource usage
- Implement SLA tracking

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Understanding of monitoring concepts
- Knowledge of metrics and alerting

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Monitoring and Analytics Example
   
   This example demonstrates comprehensive monitoring and analytics
   for IMAP operations in production environments.
   """
   
   import logging
   import time
   import threading
   import json
   import statistics
   from datetime import datetime, timedelta
   from typing import Dict, List, Optional, Any
   from dataclasses import dataclass, asdict
   from collections import defaultdict, deque
   from pathlib import Path
   
   from sage_imap.services.client import IMAPClient
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
   
   
   @dataclass
   class MetricPoint:
       """Individual metric data point."""
       timestamp: datetime
       value: float
       tags: Dict[str, str]
       metric_name: str
   
   
   @dataclass
   class PerformanceMetrics:
       """Performance metrics collection."""
       response_time: float
       throughput: float
       error_rate: float
       success_rate: float
       connection_count: int
       memory_usage: float
       cpu_usage: float
   
   
   @dataclass
   class OperationalMetrics:
       """Operational metrics collection."""
       total_operations: int
       successful_operations: int
       failed_operations: int
       messages_processed: int
       bytes_transferred: int
       connection_errors: int
       timeout_errors: int
   
   
   class MetricsCollector:
       """
       Comprehensive metrics collector.
       """
       
       def __init__(self, retention_period: int = 3600):
           """
           Initialize metrics collector.
           
           Args:
               retention_period: How long to retain metrics in seconds
           """
           self.retention_period = retention_period
           self.metrics = defaultdict(deque)
           self.lock = threading.Lock()
           self.start_time = time.time()
           
       def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
           """
           Record a metric value.
           """
           with self.lock:
               metric_point = MetricPoint(
                   timestamp=datetime.now(),
                   value=value,
                   tags=tags or {},
                   metric_name=metric_name
               )
               
               self.metrics[metric_name].append(metric_point)
               
               # Clean old metrics
               self._cleanup_old_metrics(metric_name)
       
       def _cleanup_old_metrics(self, metric_name: str):
           """
           Clean up old metrics beyond retention period.
           """
           cutoff_time = datetime.now() - timedelta(seconds=self.retention_period)
           metric_queue = self.metrics[metric_name]
           
           while metric_queue and metric_queue[0].timestamp < cutoff_time:
               metric_queue.popleft()
       
       def get_metric_values(self, metric_name: str, since: datetime = None) -> List[float]:
           """
           Get metric values for a given time period.
           """
           with self.lock:
               metric_queue = self.metrics[metric_name]
               if not since:
                   since = datetime.now() - timedelta(seconds=300)  # Last 5 minutes
               
               return [
                   point.value for point in metric_queue
                   if point.timestamp >= since
               ]
       
       def get_metric_statistics(self, metric_name: str, since: datetime = None) -> Dict[str, float]:
           """
           Get statistical summary of metric values.
           """
           values = self.get_metric_values(metric_name, since)
           
           if not values:
               return {}
           
           return {
               'count': len(values),
               'mean': statistics.mean(values),
               'median': statistics.median(values),
               'min': min(values),
               'max': max(values),
               'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
           }
   
   
   class PerformanceMonitor:
       """
       Performance monitoring system.
       """
       
       def __init__(self, metrics_collector: MetricsCollector):
           self.metrics_collector = metrics_collector
           self.operation_times = defaultdict(list)
           self.resource_monitor = ResourceMonitor()
           
       def time_operation(self, operation_name: str):
           """
           Context manager for timing operations.
           """
           return OperationTimer(self, operation_name)
       
       def record_operation_time(self, operation_name: str, duration: float):
           """
           Record operation timing.
           """
           self.metrics_collector.record_metric(
               f"operation_time_{operation_name}",
               duration,
               tags={'operation': operation_name}
           )
           
           # Keep recent timings for throughput calculation
           self.operation_times[operation_name].append({
               'timestamp': time.time(),
               'duration': duration
           })
       
       def get_performance_metrics(self) -> PerformanceMetrics:
           """
           Get current performance metrics.
           """
           now = time.time()
           
           # Calculate response times
           response_times = []
           for operation_times in self.operation_times.values():
               recent_times = [
                   t['duration'] for t in operation_times
                   if now - t['timestamp'] < 300  # Last 5 minutes
               ]
               response_times.extend(recent_times)
           
           avg_response_time = statistics.mean(response_times) if response_times else 0.0
           
           # Calculate throughput
           total_recent_ops = sum(
               len([t for t in times if now - t['timestamp'] < 60])  # Last minute
               for times in self.operation_times.values()
           )
           throughput = total_recent_ops / 60.0  # ops per second
           
           # Get resource metrics
           resource_metrics = self.resource_monitor.get_metrics()
           
           return PerformanceMetrics(
               response_time=avg_response_time,
               throughput=throughput,
               error_rate=self._calculate_error_rate(),
               success_rate=self._calculate_success_rate(),
               connection_count=resource_metrics.get('connection_count', 0),
               memory_usage=resource_metrics.get('memory_usage', 0.0),
               cpu_usage=resource_metrics.get('cpu_usage', 0.0)
           )
       
       def _calculate_error_rate(self) -> float:
           """Calculate current error rate."""
           error_values = self.metrics_collector.get_metric_values('error_count')
           total_values = self.metrics_collector.get_metric_values('total_operations')
           
           if not total_values:
               return 0.0
           
           recent_errors = sum(error_values[-10:])  # Last 10 measurements
           recent_total = sum(total_values[-10:])
           
           return (recent_errors / recent_total) * 100 if recent_total > 0 else 0.0
       
       def _calculate_success_rate(self) -> float:
           """Calculate current success rate."""
           return 100.0 - self._calculate_error_rate()
   
   
   class OperationTimer:
       """
       Context manager for timing operations.
       """
       
       def __init__(self, monitor: PerformanceMonitor, operation_name: str):
           self.monitor = monitor
           self.operation_name = operation_name
           self.start_time = None
       
       def __enter__(self):
           self.start_time = time.time()
           return self
       
       def __exit__(self, exc_type, exc_val, exc_tb):
           if self.start_time:
               duration = time.time() - self.start_time
               self.monitor.record_operation_time(self.operation_name, duration)
   
   
   class ResourceMonitor:
       """
       System resource monitoring.
       """
       
       def __init__(self):
           self.connection_count = 0
           
       def get_metrics(self) -> Dict[str, float]:
           """
           Get current resource metrics.
           """
           import psutil
           
           # Get process info
           process = psutil.Process()
           
           return {
               'memory_usage': process.memory_info().rss / 1024 / 1024,  # MB
               'cpu_usage': process.cpu_percent(),
               'connection_count': self.connection_count,
               'thread_count': process.num_threads(),
               'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0
           }
       
       def increment_connections(self):
           """Increment connection count."""
           self.connection_count += 1
       
       def decrement_connections(self):
           """Decrement connection count."""
           self.connection_count = max(0, self.connection_count - 1)
   
   
   class AlertingSystem:
       """
       Alerting system for monitoring thresholds.
       """
       
       def __init__(self, metrics_collector: MetricsCollector):
           self.metrics_collector = metrics_collector
           self.alert_rules = []
           self.alert_history = []
           self.notification_channels = []
           
       def add_alert_rule(self, rule: 'AlertRule'):
           """Add an alert rule."""
           self.alert_rules.append(rule)
       
       def add_notification_channel(self, channel: 'NotificationChannel'):
           """Add a notification channel."""
           self.notification_channels.append(channel)
       
       def check_alerts(self):
           """Check all alert rules."""
           for rule in self.alert_rules:
               if rule.should_alert(self.metrics_collector):
                   alert = Alert(
                       rule_name=rule.name,
                       message=rule.get_alert_message(self.metrics_collector),
                       severity=rule.severity,
                       timestamp=datetime.now()
                   )
                   
                   self.alert_history.append(alert)
                   self.send_alert(alert)
       
       def send_alert(self, alert: 'Alert'):
           """Send alert through notification channels."""
           for channel in self.notification_channels:
               try:
                   channel.send(alert)
               except Exception as e:
                   logger.error(f"Failed to send alert through {channel}: {e}")
   
   
   @dataclass
   class Alert:
       """Alert information."""
       rule_name: str
       message: str
       severity: str
       timestamp: datetime
   
   
   class AlertRule:
       """
       Alert rule definition.
       """
       
       def __init__(self, name: str, metric_name: str, threshold: float, 
                    operator: str = '>', severity: str = 'warning'):
           self.name = name
           self.metric_name = metric_name
           self.threshold = threshold
           self.operator = operator
           self.severity = severity
           self.last_alert_time = None
           self.cooldown_period = 300  # 5 minutes
           
       def should_alert(self, metrics_collector: MetricsCollector) -> bool:
           """Check if alert should be triggered."""
           # Check cooldown period
           if self.last_alert_time:
               time_since_last = (datetime.now() - self.last_alert_time).total_seconds()
               if time_since_last < self.cooldown_period:
                   return False
           
           # Get recent metric values
           values = metrics_collector.get_metric_values(self.metric_name)
           if not values:
               return False
           
           current_value = values[-1]  # Most recent value
           
           # Check threshold
           if self.operator == '>':
               triggered = current_value > self.threshold
           elif self.operator == '<':
               triggered = current_value < self.threshold
           elif self.operator == '>=':
               triggered = current_value >= self.threshold
           elif self.operator == '<=':
               triggered = current_value <= self.threshold
           else:
               return False
           
           if triggered:
               self.last_alert_time = datetime.now()
           
           return triggered
       
       def get_alert_message(self, metrics_collector: MetricsCollector) -> str:
           """Get alert message."""
           values = metrics_collector.get_metric_values(self.metric_name)
           current_value = values[-1] if values else 0
           
           return (f"Alert: {self.name} - {self.metric_name} is {current_value} "
                   f"({self.operator} {self.threshold})")
   
   
   class NotificationChannel:
       """
       Base notification channel.
       """
       
       def send(self, alert: Alert):
           """Send alert notification."""
           raise NotImplementedError
   
   
   class LogNotificationChannel(NotificationChannel):
       """
       Log-based notification channel.
       """
       
       def send(self, alert: Alert):
           """Send alert to log."""
           logger.warning(f"ALERT [{alert.severity.upper()}] {alert.message}")
   
   
   class MonitoringAnalyticsExample:
       """
       Comprehensive monitoring and analytics example.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize monitoring and analytics example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
           # Initialize monitoring components
           self.metrics_collector = MetricsCollector()
           self.performance_monitor = PerformanceMonitor(self.metrics_collector)
           self.alerting_system = AlertingSystem(self.metrics_collector)
           self.resource_monitor = ResourceMonitor()
           
           # Setup alerting
           self.setup_alerting()
           
           # Monitoring thread
           self.monitoring_thread = None
           self.monitoring_active = False
           
       def setup_alerting(self):
           """Setup alerting rules and channels."""
           # Add alert rules
           self.alerting_system.add_alert_rule(
               AlertRule("High Error Rate", "error_rate", 5.0, ">", "critical")
           )
           
           self.alerting_system.add_alert_rule(
               AlertRule("High Response Time", "avg_response_time", 2.0, ">", "warning")
           )
           
           self.alerting_system.add_alert_rule(
               AlertRule("Low Success Rate", "success_rate", 95.0, "<", "warning")
           )
           
           # Add notification channels
           self.alerting_system.add_notification_channel(LogNotificationChannel())
           
       def demonstrate_monitoring_analytics(self):
           """
           Demonstrate comprehensive monitoring and analytics.
           """
           logger.info("=== Monitoring and Analytics Example ===")
           
           try:
               # Start monitoring
               self.start_monitoring()
               
               # Simulate operations with monitoring
               self.simulate_operations_with_monitoring()
               
               # Performance analysis
               self.demonstrate_performance_analysis()
               
               # Metrics collection
               self.demonstrate_metrics_collection()
               
               # Analytics and reporting
               self.demonstrate_analytics_reporting()
               
               # SLA monitoring
               self.demonstrate_sla_monitoring()
               
               # Dashboard data
               self.demonstrate_dashboard_data()
               
               logger.info("✓ Monitoring and analytics completed successfully")
               
           except Exception as e:
               logger.error(f"❌ Monitoring and analytics failed: {e}")
               raise
           finally:
               # Stop monitoring
               self.stop_monitoring()
       
       def start_monitoring(self):
           """Start monitoring thread."""
           self.monitoring_active = True
           self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
           self.monitoring_thread.start()
           logger.info("Monitoring started")
       
       def stop_monitoring(self):
           """Stop monitoring thread."""
           self.monitoring_active = False
           if self.monitoring_thread:
               self.monitoring_thread.join(timeout=5.0)
           logger.info("Monitoring stopped")
       
       def monitoring_loop(self):
           """Main monitoring loop."""
           while self.monitoring_active:
               try:
                   # Collect metrics
                   self.collect_system_metrics()
                   
                   # Check alerts
                   self.alerting_system.check_alerts()
                   
                   # Sleep for monitoring interval
                   time.sleep(10.0)
                   
               except Exception as e:
                   logger.error(f"Monitoring loop error: {e}")
       
       def collect_system_metrics(self):
           """Collect system metrics."""
           # Get resource metrics
           resource_metrics = self.resource_monitor.get_metrics()
           
           # Record metrics
           for metric_name, value in resource_metrics.items():
               self.metrics_collector.record_metric(metric_name, value)
           
           # Get performance metrics
           perf_metrics = self.performance_monitor.get_performance_metrics()
           
           # Record performance metrics
           self.metrics_collector.record_metric('response_time', perf_metrics.response_time)
           self.metrics_collector.record_metric('throughput', perf_metrics.throughput)
           self.metrics_collector.record_metric('error_rate', perf_metrics.error_rate)
           self.metrics_collector.record_metric('success_rate', perf_metrics.success_rate)
       
       def simulate_operations_with_monitoring(self):
           """Simulate IMAP operations with monitoring."""
           logger.info("--- Simulating Operations with Monitoring ---")
           
           try:
               with IMAPClient(config=self.config) as client:
                   self.resource_monitor.increment_connections()
                   
                   try:
                       uid_service = IMAPMailboxUIDService(client)
                       
                       # Simulate various operations
                       operations = [
                           ("select_inbox", lambda: uid_service.select("INBOX")),
                           ("get_status", lambda: uid_service.get_mailbox_status()),
                           ("search_messages", lambda: uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)),
                           ("count_messages", lambda: len(uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)))
                       ]
                       
                       for op_name, operation in operations:
                           for i in range(5):  # Repeat each operation
                               try:
                                   with self.performance_monitor.time_operation(op_name):
                                       result = operation()
                                       
                                       # Record successful operation
                                       self.metrics_collector.record_metric('successful_operations', 1)
                                       logger.info(f"    ✓ {op_name} completed")
                                       
                                       # Brief pause
                                       time.sleep(0.1)
                               
                               except Exception as e:
                                   # Record failed operation
                                   self.metrics_collector.record_metric('failed_operations', 1)
                                   logger.error(f"    ❌ {op_name} failed: {e}")
                   
                   finally:
                       self.resource_monitor.decrement_connections()
               
               logger.info("✓ Operations simulation completed")
               
           except Exception as e:
               logger.error(f"Failed operations simulation: {e}")
       
       def demonstrate_performance_analysis(self):
           """Demonstrate performance analysis."""
           logger.info("--- Performance Analysis ---")
           
           try:
               # Get performance metrics
               perf_metrics = self.performance_monitor.get_performance_metrics()
               
               logger.info("📊 Performance Metrics:")
               logger.info(f"  • Response Time: {perf_metrics.response_time:.3f}s")
               logger.info(f"  • Throughput: {perf_metrics.throughput:.2f} ops/s")
               logger.info(f"  • Error Rate: {perf_metrics.error_rate:.2f}%")
               logger.info(f"  • Success Rate: {perf_metrics.success_rate:.2f}%")
               logger.info(f"  • Active Connections: {perf_metrics.connection_count}")
               logger.info(f"  • Memory Usage: {perf_metrics.memory_usage:.1f}MB")
               logger.info(f"  • CPU Usage: {perf_metrics.cpu_usage:.1f}%")
               
               # Analyze trends
               self.analyze_performance_trends()
               
               logger.info("✓ Performance analysis completed")
               
           except Exception as e:
               logger.error(f"Failed performance analysis: {e}")
       
       def analyze_performance_trends(self):
           """Analyze performance trends."""
           logger.info("--- Performance Trends ---")
           
           try:
               # Analyze response time trends
               response_times = self.metrics_collector.get_metric_values('response_time')
               
               if len(response_times) >= 2:
                   recent_avg = statistics.mean(response_times[-5:])
                   earlier_avg = statistics.mean(response_times[-10:-5]) if len(response_times) >= 10 else recent_avg
                   
                   trend = "improving" if recent_avg < earlier_avg else "degrading"
                   logger.info(f"  • Response Time Trend: {trend}")
                   logger.info(f"    Recent: {recent_avg:.3f}s, Earlier: {earlier_avg:.3f}s")
               
               # Analyze throughput trends
               throughput_values = self.metrics_collector.get_metric_values('throughput')
               
               if len(throughput_values) >= 2:
                   recent_throughput = statistics.mean(throughput_values[-5:])
                   earlier_throughput = statistics.mean(throughput_values[-10:-5]) if len(throughput_values) >= 10 else recent_throughput
                   
                   trend = "improving" if recent_throughput > earlier_throughput else "degrading"
                   logger.info(f"  • Throughput Trend: {trend}")
                   logger.info(f"    Recent: {recent_throughput:.2f} ops/s, Earlier: {earlier_throughput:.2f} ops/s")
               
           except Exception as e:
               logger.error(f"Failed performance trends analysis: {e}")
       
       def demonstrate_metrics_collection(self):
           """Demonstrate metrics collection capabilities."""
           logger.info("--- Metrics Collection ---")
           
           try:
               # Show available metrics
               available_metrics = list(self.metrics_collector.metrics.keys())
               logger.info(f"📊 Available Metrics ({len(available_metrics)}):")
               
               for metric_name in available_metrics:
                   stats = self.metrics_collector.get_metric_statistics(metric_name)
                   
                   if stats:
                       logger.info(f"  • {metric_name}:")
                       logger.info(f"    Count: {stats['count']}")
                       logger.info(f"    Mean: {stats['mean']:.3f}")
                       logger.info(f"    Min/Max: {stats['min']:.3f}/{stats['max']:.3f}")
                       logger.info(f"    Std Dev: {stats['std_dev']:.3f}")
               
               logger.info("✓ Metrics collection demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed metrics collection: {e}")
       
       def demonstrate_analytics_reporting(self):
           """Demonstrate analytics and reporting."""
           logger.info("--- Analytics and Reporting ---")
           
           try:
               # Generate analytics report
               report = self.generate_analytics_report()
               
               logger.info("📈 Analytics Report:")
               logger.info("=" * 50)
               logger.info(f"Report Period: {report['period']}")
               logger.info(f"Total Operations: {report['total_operations']}")
               logger.info(f"Success Rate: {report['success_rate']:.2f}%")
               logger.info(f"Average Response Time: {report['avg_response_time']:.3f}s")
               logger.info(f"Peak Throughput: {report['peak_throughput']:.2f} ops/s")
               
               # Top operations by frequency
               if report['top_operations']:
                   logger.info("Top Operations:")
                   for op_name, count in report['top_operations'].items():
                       logger.info(f"  • {op_name}: {count} times")
               
               # Performance insights
               insights = self.generate_performance_insights(report)
               if insights:
                   logger.info("Performance Insights:")
                   for insight in insights:
                       logger.info(f"  • {insight}")
               
               logger.info("=" * 50)
               
               logger.info("✓ Analytics and reporting completed")
               
           except Exception as e:
               logger.error(f"Failed analytics and reporting: {e}")
       
       def generate_analytics_report(self) -> Dict[str, Any]:
           """Generate comprehensive analytics report."""
           # Calculate report metrics
           successful_ops = sum(self.metrics_collector.get_metric_values('successful_operations'))
           failed_ops = sum(self.metrics_collector.get_metric_values('failed_operations'))
           total_ops = successful_ops + failed_ops
           
           success_rate = (successful_ops / total_ops * 100) if total_ops > 0 else 0
           
           response_times = self.metrics_collector.get_metric_values('response_time')
           avg_response_time = statistics.mean(response_times) if response_times else 0
           
           throughput_values = self.metrics_collector.get_metric_values('throughput')
           peak_throughput = max(throughput_values) if throughput_values else 0
           
           return {
               'period': f"Last {self.metrics_collector.retention_period} seconds",
               'total_operations': total_ops,
               'successful_operations': successful_ops,
               'failed_operations': failed_ops,
               'success_rate': success_rate,
               'avg_response_time': avg_response_time,
               'peak_throughput': peak_throughput,
               'top_operations': self.get_top_operations(),
               'timestamp': datetime.now().isoformat()
           }
       
       def get_top_operations(self) -> Dict[str, int]:
           """Get top operations by frequency."""
           operation_counts = {}
           
           for metric_name in self.metrics_collector.metrics.keys():
               if metric_name.startswith('operation_time_'):
                   operation = metric_name.replace('operation_time_', '')
                   count = len(self.metrics_collector.get_metric_values(metric_name))
                   operation_counts[operation] = count
           
           # Sort by count
           return dict(sorted(operation_counts.items(), key=lambda x: x[1], reverse=True))
       
       def generate_performance_insights(self, report: Dict[str, Any]) -> List[str]:
           """Generate performance insights."""
           insights = []
           
           # Success rate insights
           if report['success_rate'] < 95:
               insights.append(f"Low success rate ({report['success_rate']:.1f}%) - investigate failures")
           elif report['success_rate'] > 99:
               insights.append("Excellent success rate - system performing well")
           
           # Response time insights
           if report['avg_response_time'] > 1.0:
               insights.append(f"High response time ({report['avg_response_time']:.3f}s) - consider optimization")
           elif report['avg_response_time'] < 0.1:
               insights.append("Excellent response time - system highly optimized")
           
           # Throughput insights
           if report['peak_throughput'] > 10:
               insights.append(f"High throughput achieved ({report['peak_throughput']:.1f} ops/s)")
           elif report['peak_throughput'] < 1:
               insights.append("Low throughput - investigate bottlenecks")
           
           return insights
       
       def demonstrate_sla_monitoring(self):
           """Demonstrate SLA monitoring."""
           logger.info("--- SLA Monitoring ---")
           
           try:
               # Define SLA targets
               sla_targets = {
                   'availability': 99.9,  # 99.9% uptime
                   'response_time': 0.5,  # 500ms average response time
                   'success_rate': 99.5,  # 99.5% success rate
                   'throughput': 5.0      # 5 ops/s minimum throughput
               }
               
               # Check SLA compliance
               current_metrics = self.performance_monitor.get_performance_metrics()
               
               sla_status = {}
               
               # Check response time SLA
               sla_status['response_time'] = {
                   'target': sla_targets['response_time'],
                   'actual': current_metrics.response_time,
                   'compliant': current_metrics.response_time <= sla_targets['response_time']
               }
               
               # Check success rate SLA
               sla_status['success_rate'] = {
                   'target': sla_targets['success_rate'],
                   'actual': current_metrics.success_rate,
                   'compliant': current_metrics.success_rate >= sla_targets['success_rate']
               }
               
               # Check throughput SLA
               sla_status['throughput'] = {
                   'target': sla_targets['throughput'],
                   'actual': current_metrics.throughput,
                   'compliant': current_metrics.throughput >= sla_targets['throughput']
               }
               
               # Report SLA status
               logger.info("🎯 SLA Status:")
               overall_compliance = True
               
               for metric_name, status in sla_status.items():
                   compliance_status = "✓" if status['compliant'] else "❌"
                   logger.info(f"  • {metric_name}: {compliance_status}")
                   logger.info(f"    Target: {status['target']}, Actual: {status['actual']:.3f}")
                   
                   if not status['compliant']:
                       overall_compliance = False
               
               compliance_percentage = sum(1 for s in sla_status.values() if s['compliant']) / len(sla_status) * 100
               logger.info(f"Overall SLA Compliance: {compliance_percentage:.1f}%")
               
               logger.info("✓ SLA monitoring completed")
               
           except Exception as e:
               logger.error(f"Failed SLA monitoring: {e}")
       
       def demonstrate_dashboard_data(self):
           """Demonstrate dashboard data generation."""
           logger.info("--- Dashboard Data ---")
           
           try:
               # Generate dashboard data
               dashboard_data = self.generate_dashboard_data()
               
               logger.info("📊 Dashboard Data Generated:")
               logger.info(f"  • Real-time metrics: {len(dashboard_data['real_time_metrics'])} points")
               logger.info(f"  • Historical data: {len(dashboard_data['historical_data'])} points")
               logger.info(f"  • Active alerts: {len(dashboard_data['active_alerts'])}")
               logger.info(f"  • System health: {dashboard_data['system_health']['status']}")
               
               # Sample dashboard data (would be sent to dashboard)
               logger.info("Sample Dashboard JSON:")
               sample_data = {
                   'timestamp': dashboard_data['timestamp'],
                   'system_health': dashboard_data['system_health'],
                   'key_metrics': dashboard_data['key_metrics']
               }
               
               logger.info(json.dumps(sample_data, indent=2))
               
               logger.info("✓ Dashboard data generation completed")
               
           except Exception as e:
               logger.error(f"Failed dashboard data generation: {e}")
       
       def generate_dashboard_data(self) -> Dict[str, Any]:
           """Generate data for dashboard consumption."""
           current_metrics = self.performance_monitor.get_performance_metrics()
           
           # Real-time metrics
           real_time_metrics = []
           for metric_name in ['response_time', 'throughput', 'error_rate']:
               values = self.metrics_collector.get_metric_values(metric_name)
               if values:
                   real_time_metrics.extend([
                       {'metric': metric_name, 'value': value, 'timestamp': time.time()}
                       for value in values[-10:]  # Last 10 values
                   ])
           
           # Historical data
           historical_data = []
           for metric_name in self.metrics_collector.metrics.keys():
               stats = self.metrics_collector.get_metric_statistics(metric_name)
               if stats:
                   historical_data.append({
                       'metric': metric_name,
                       'statistics': stats,
                       'timestamp': time.time()
                   })
           
           # Active alerts
           active_alerts = [
               {
                   'rule': alert.rule_name,
                   'message': alert.message,
                   'severity': alert.severity,
                   'timestamp': alert.timestamp.isoformat()
               }
               for alert in self.alerting_system.alert_history[-5:]  # Last 5 alerts
           ]
           
           # System health
           system_health = {
               'status': 'healthy' if current_metrics.success_rate > 95 else 'degraded',
               'response_time': current_metrics.response_time,
               'success_rate': current_metrics.success_rate,
               'throughput': current_metrics.throughput
           }
           
           return {
               'timestamp': datetime.now().isoformat(),
               'real_time_metrics': real_time_metrics,
               'historical_data': historical_data,
               'active_alerts': active_alerts,
               'system_health': system_health,
               'key_metrics': {
                   'response_time': current_metrics.response_time,
                   'throughput': current_metrics.throughput,
                   'success_rate': current_metrics.success_rate,
                   'error_rate': current_metrics.error_rate
               }
           }


   def main():
       """
       Main function to run the monitoring and analytics example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = MonitoringAnalyticsExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_monitoring_analytics()
           logger.info("🎉 Monitoring and analytics example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Metrics Collection
------------------

Core Metrics
~~~~~~~~~~~~

.. code-block:: python

   # Performance metrics
   metrics_collector.record_metric('response_time', duration)
   metrics_collector.record_metric('throughput', ops_per_second)
   metrics_collector.record_metric('error_rate', error_percentage)
   
   # Operational metrics
   metrics_collector.record_metric('messages_processed', count)
   metrics_collector.record_metric('bytes_transferred', bytes_count)
   metrics_collector.record_metric('connection_errors', error_count)

Custom Metrics
~~~~~~~~~~~~~~

.. code-block:: python

   # Business metrics
   metrics_collector.record_metric('emails_categorized', count)
   metrics_collector.record_metric('attachments_processed', count)
   metrics_collector.record_metric('spam_detected', count)
   
   # Resource metrics
   metrics_collector.record_metric('memory_usage', memory_mb)
   metrics_collector.record_metric('cpu_usage', cpu_percent)
   metrics_collector.record_metric('disk_usage', disk_percent)

Alerting System
---------------

Alert Rules
~~~~~~~~~~~

.. code-block:: python

   # Response time alert
   alert_rule = AlertRule(
       name="High Response Time",
       metric_name="response_time",
       threshold=2.0,
       operator=">",
       severity="warning"
   )
   
   # Error rate alert
   error_alert = AlertRule(
       name="High Error Rate",
       metric_name="error_rate",
       threshold=5.0,
       operator=">",
       severity="critical"
   )

Notification Channels
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Email notifications
   class EmailNotificationChannel(NotificationChannel):
       def send(self, alert: Alert):
           send_email(
               to="admin@company.com",
               subject=f"Alert: {alert.rule_name}",
               body=alert.message
           )
   
   # Slack notifications
   class SlackNotificationChannel(NotificationChannel):
       def send(self, alert: Alert):
           send_slack_message(
               channel="#alerts",
               message=f"🚨 {alert.message}"
           )

Performance Monitoring
----------------------

Operation Timing
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Time operations
   with performance_monitor.time_operation('search_messages'):
       messages = uid_service.create_message_set_from_search(criteria)
   
   # Manual timing
   start_time = time.time()
   result = perform_operation()
   duration = time.time() - start_time
   performance_monitor.record_operation_time('operation_name', duration)

Resource Monitoring
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Monitor system resources
   import psutil
   
   def get_system_metrics():
       return {
           'cpu_usage': psutil.cpu_percent(),
           'memory_usage': psutil.virtual_memory().percent,
           'disk_usage': psutil.disk_usage('/').percent,
           'network_io': psutil.net_io_counters(),
           'process_count': len(psutil.pids())
       }

Analytics and Reporting
-----------------------

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get metric statistics
   stats = metrics_collector.get_metric_statistics('response_time')
   
   print(f"Average response time: {stats['mean']:.3f}s")
   print(f"95th percentile: {stats['p95']:.3f}s")
   print(f"Standard deviation: {stats['std_dev']:.3f}s")

Trend Analysis
~~~~~~~~~~~~~~

.. code-block:: python

   # Analyze trends
   def analyze_trend(metric_name, window_size=10):
       values = metrics_collector.get_metric_values(metric_name)
       
       if len(values) < window_size * 2:
           return "insufficient_data"
       
       recent_avg = statistics.mean(values[-window_size:])
       previous_avg = statistics.mean(values[-window_size*2:-window_size])
       
       if recent_avg > previous_avg * 1.1:
           return "increasing"
       elif recent_avg < previous_avg * 0.9:
           return "decreasing"
       else:
           return "stable"

Dashboard Integration
---------------------

Real-time Data
~~~~~~~~~~~~~~

.. code-block:: python

   # Generate real-time dashboard data
   def get_dashboard_data():
       return {
           'timestamp': datetime.now().isoformat(),
           'metrics': {
               'response_time': get_current_response_time(),
               'throughput': get_current_throughput(),
               'error_rate': get_current_error_rate(),
               'success_rate': get_current_success_rate()
           },
           'alerts': get_active_alerts(),
           'system_health': get_system_health()
       }

Visualization Data
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Time series data for charts
   def get_time_series_data(metric_name, duration_minutes=60):
       end_time = datetime.now()
       start_time = end_time - timedelta(minutes=duration_minutes)
       
       values = metrics_collector.get_metric_values(metric_name, since=start_time)
       
       return [
           {
               'timestamp': point.timestamp.isoformat(),
               'value': point.value
           }
           for point in values
       ]

Best Practices
--------------

✅ **DO:**

- Collect metrics consistently

- Monitor key performance indicators

- Set up meaningful alerts

- Analyze trends and patterns

- Generate regular reports

- Use appropriate retention periods

- Monitor system resources

- Implement SLA tracking

❌ **DON'T:**

- Over-collect metrics

- Ignore alert fatigue

- Skip trend analysis

- Forget to clean up old data

- Ignore resource usage

- Set up too many alerts

- Skip performance baselines

- Forget to monitor the monitoring system

Monitoring Stack
----------------

Prometheus Integration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from prometheus_client import Counter, Histogram, Gauge
   
   # Define metrics
   operation_counter = Counter('imap_operations_total', 'Total operations')
   response_time = Histogram('imap_response_time_seconds', 'Response time')
   active_connections = Gauge('imap_active_connections', 'Active connections')
   
   # Record metrics
   operation_counter.inc()
   response_time.observe(duration)
   active_connections.set(connection_count)

Grafana Dashboards
~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "dashboard": {
       "title": "IMAP Service Monitoring",
       "panels": [
         {
           "title": "Response Time",
           "type": "graph",
           "targets": [
             {
               "expr": "imap_response_time_seconds",
               "legendFormat": "Response Time"
             }
           ]
         },
         {
           "title": "Throughput",
           "type": "graph",
           "targets": [
             {
               "expr": "rate(imap_operations_total[5m])",
               "legendFormat": "Operations/sec"
             }
           ]
         }
       ]
     }
   }

Next Steps
----------

For more advanced patterns, see:

- :doc:`production_patterns` - Production deployment patterns
- :doc:`error_handling` - Error handling strategies
- :doc:`client_advanced` - Advanced client features
- :doc:`large_volume_handling` - High-performance processing 