from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
import time
from config import Config
from functools import wraps
from typing import Callable, Any
import asyncio
import psutil

class MetricsCollector:
    def __init__(self):
        # Initialize Prometheus metrics
        self.processed_validations = Counter(
            'validation_processed_total',
            'Total number of validations processed',
            ['pc_id', 'service_type', 'status']
        )
        
        self.api_requests = Counter(
            'validation_api_requests_total',
            'Total number of validation API requests made',
            ['pc_id', 'service_type', 'endpoint']
        )
        
        self.validation_errors = Counter(
            'validation_errors_total',
            'Total number of validation errors',
            ['pc_id', 'service_type', 'error_type']
        )
        
        self.current_usage = Gauge(
            'current_api_usage',
            'Current API usage count',
            ['pc_id', 'service_type']
        )
        
        self.validation_time = Histogram(
            'validation_processing_seconds',
            'Time spent processing validations',
            ['pc_id', 'service_type'],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
        )
        
        self.queue_size = Gauge(
            'validation_queue_size',
            'Current size of the validation queue',
            ['pc_id', 'queue_name']
        )
        
        self.database_operations = Summary(
            'validation_database_operation_seconds',
            'Time spent on database operations',
            ['pc_id', 'operation']
        )
        
        # Validation success rates
        self.validation_success_rate = Gauge(
            'validation_success_rate',
            'Success rate of validations',
            ['pc_id', 'service_type']
        )

        # System metrics
        self.memory_usage = Gauge(
            'validation_memory_usage_bytes',
            'Current memory usage',
            ['pc_id', 'type']
        )
        
        self.cpu_usage = Gauge(
            'validation_cpu_usage_percent',
            'Current CPU usage percentage',
            ['pc_id']
        )

        # Start metrics server
        start_http_server(8000)

    def track_time(self, service_type: str) -> Callable:
        """Decorator to track time spent in functions"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    self.validation_time.labels(
                        pc_id=Config.PC_ID,
                        service_type=service_type
                    ).observe(time.time() - start_time)
                    return result
                except Exception as e:
                    self.validation_errors.labels(
                        pc_id=Config.PC_ID,
                        service_type=service_type,
                        error_type=type(e).__name__
                    ).inc()
                    raise
            return wrapper
        return decorator

    def increment_processed_validations(self, service_type: str, status: str = 'success'):
        """Increment the processed validations counter"""
        self.processed_validations.labels(
            pc_id=Config.PC_ID,
            service_type=service_type,
            status=status
        ).inc()

    def increment_api_requests(self, service_type: str, endpoint: str):
        """Increment the API requests counter"""
        self.api_requests.labels(
            pc_id=Config.PC_ID,
            service_type=service_type,
            endpoint=endpoint
        ).inc()

    def increment_validation_errors(self, service_type: str, error_type: str):
        """Increment the validation errors counter"""
        self.validation_errors.labels(
            pc_id=Config.PC_ID,
            service_type=service_type,
            error_type=error_type
        ).inc()

    def set_current_usage(self, service_type: str, value: int):
        """Set the current API usage gauge"""
        self.current_usage.labels(
            pc_id=Config.PC_ID,
            service_type=service_type
        ).set(value)

    def observe_processing_time(self, service_type: str, start_time: float):
        """Record the processing time"""
        self.validation_time.labels(
            pc_id=Config.PC_ID,
            service_type=service_type
        ).observe(time.time() - start_time)

    def update_success_rate(self, service_type: str, success_count: int, total_count: int):
        """Update the success rate gauge"""
        if total_count > 0:
            rate = (success_count / total_count) * 100
            self.validation_success_rate.labels(
                pc_id=Config.PC_ID,
                service_type=service_type
            ).set(rate)

    def set_queue_size(self, queue_name: str, size: int):
        """Set the current queue size"""
        self.queue_size.labels(
            pc_id=Config.PC_ID,
            queue_name=queue_name
        ).set(size)

    async def collect_metrics(self):
        """Background task to collect system metrics periodically"""
        while True:
            try:
                process = psutil.Process()
                
                # Memory metrics
                memory_info = process.memory_info()
                self.memory_usage.labels(
                    pc_id=Config.PC_ID,
                    type='rss'
                ).set(memory_info.rss)
                
                self.memory_usage.labels(
                    pc_id=Config.PC_ID,
                    type='vms'
                ).set(memory_info.vms)
                
                # CPU metrics
                self.cpu_usage.labels(
                    pc_id=Config.PC_ID
                ).set(process.cpu_percent())
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                self.increment_validation_errors('system', f"metrics_collection_{type(e).__name__}")
                await asyncio.sleep(60)