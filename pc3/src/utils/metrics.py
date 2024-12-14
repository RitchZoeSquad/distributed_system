from prometheus_client import Counter, Gauge, Summary
import psutil
import time

class MetricsCollector:
    def __init__(self):
        # Message processing metrics
        self.messages_processed = Counter(
            'messages_processed_total',
            'Total number of messages processed'
        )
        self.message_processing_time = Summary(
            'message_processing_seconds',
            'Time spent processing messages'
        )
        
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage',
            'Current system CPU usage'
        )
        self.memory_usage = Gauge(
            'system_memory_usage_bytes',
            'Current system memory usage in bytes'
        )

    def record_message_processed(self):
        """Record a processed message"""
        self.messages_processed.inc()

    def time_message_processing(self):
        """Context manager for timing message processing"""
        return self.message_processing_time.time()

    def update_system_metrics(self):
        """Update system metrics"""
        self.cpu_usage.set(psutil.cpu_percent())
        self.memory_usage.set(psutil.Process().memory_info().rss)

# Create a singleton instance
metrics = MetricsCollector()