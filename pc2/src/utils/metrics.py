from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
import time
from config import Config
from functools import wraps
from typing import Callable, Any
import asyncio

class MetricsCollector:
    def __init__(self):
        # Initialize Prometheus metrics
        self.processed_businesses = Counter(
            'processed_businesses_total',
            'Total number of businesses processed',
            ['pc_id', 'status']
        )
        
        self.api_requests = Counter(
            'api_requests_total',
            'Total number of API requests made',
            ['pc_id', 'endpoint']
        )
        
        self.api_errors = Counter(
            'api_errors_total',
            'Total number of API errors',
            ['pc_id', 'error_type']
        )
        
        self.current_usage = Gauge(
            'current_api_usage',
            'Current API usage count',
            ['pc_id']
        )
        
        self.processing_time = Histogram(
            'business_processing_seconds',
            'Time spent processing businesses',
            ['pc_id'],
            buckets=(1, 2, 5, 10, 30, 60, 120, 300)
        )
        
        self.queue_size = Gauge(
            'queue_size',
            'Current size of the processing queue',
            ['pc_id', 'queue_name']
        )
        
        self.database_operations = Summary(
            'database_operation_seconds',
            'Time spent on database operations',
            ['pc_id', 'operation']
        )

        # Memory metrics
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Current memory usage',
            ['pc_id', 'type']
        )

        # Start metrics server
        start_http_server(8000)

    def track_time(self, metric_name: str) -> Callable:
        """Decorator to track time spent in functions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    self.database_operations.labels(
                        pc_id=Config.PC_ID,
                        operation=metric_name
                    ).observe(time.time() - start_time)
                    return result
                except Exception as e:
                    self.api_errors.labels(
                        pc_id=Config.PC_ID,
                        error_type=type(e).__name__
                    ).inc()
                    raise
            return wrapper
        return decorator

    def increment_processed_businesses(self, status: str = 'success'):
        """Increment the processed businesses counter"""
        self.processed_businesses.labels(
            pc_id=Config.PC_ID,
            status=status
        ).inc()

    def increment_api_requests(self, endpoint: str):
        """Increment the API requests counter"""
        self.api_requests.labels(
            pc_id=Config.PC_ID,
            endpoint=endpoint
        ).inc()

    def increment_api_errors(self, error_type: str):
        """Increment the API errors counter"""
        self.api_errors.labels(
            pc_id=Config.PC_ID,
            error_type=error_type
        ).inc()

    def set_current_usage(self, value: int):
        """Set the current API usage gauge"""
        self.current_usage.labels(
            pc_id=Config.PC_ID
        ).set(value)

    def observe_processing_time(self, start_time: float):
        """Record the processing time for a business"""
        self.processing_time.labels(
            pc_id=Config.PC_ID
        ).observe(time.time() - start_time)

    def set_queue_size(self, queue_name: str, size: int):
        """Set the current queue size"""
        self.queue_size.labels(
            pc_id=Config.PC_ID,
            queue_name=queue_name
        ).set(size)

    def time(self) -> float:
        """Get current time for timing operations"""
        return time.time()

    async def collect_metrics(self):
        """Background task to collect metrics periodically"""
        while True:
            try:
                # Update system metrics
                self.update_memory_metrics()
                
                # Sleep for 60 seconds
                await asyncio.sleep(60)
            except Exception as e:
                self.increment_api_errors(f"metrics_collection_{type(e).__name__}")
                await asyncio.sleep(60)

    def update_memory_metrics(self):
        """Update memory usage metrics"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            self.memory_usage.labels(
                pc_id=Config.PC_ID,
                type='rss'
            ).set(memory_info.rss)
            
            self.memory_usage.labels(
                pc_id=Config.PC_ID,
                type='vms'
            ).set(memory_info.vms)
        except Exception as e:
            self.increment_api_errors(f"memory_metrics_{type(e).__name__}")