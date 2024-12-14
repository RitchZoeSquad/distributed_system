from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
import time
from config import Config
from functools import wraps
from typing import Callable, Any
import asyncio
import psutil
import os

class MetricsCollector:
    def __init__(self):
        # Get metrics port from environment
        self.metrics_port = int(os.getenv('METRICS_PORT', '8000'))
        
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
            'Current API usage percentage',
            ['pc_id', 'service_type', 'api_type']
        )
        
        self.processing_time = Histogram(
            'validation_processing_seconds',
            'Time spent processing validations',
            ['pc_id', 'service_type'],
            buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
        )
        
        self.system_metrics = {
            'cpu_usage': Gauge('system_cpu_usage', 'Current CPU usage percentage', ['pc_id']),
            'memory_usage': Gauge('system_memory_usage', 'Current memory usage percentage', ['pc_id']),
            'disk_usage': Gauge('system_disk_usage', 'Current disk usage percentage', ['pc_id'])
        }
        
        # Start metrics collection
        self.start_metrics_collection()
    
    def start_metrics_collection(self):
        """Start collecting system metrics"""
        try:
            start_http_server(self.metrics_port)
            print(f"Started metrics server on port {self.metrics_port}")
        except Exception as e:
            print(f"Failed to start metrics server on port {self.metrics_port}: {e}")
    
    def record_validation(self, pc_id: str, service_type: str, status: str):
        """Record a validation event"""
        self.processed_validations.labels(pc_id=pc_id, service_type=service_type, status=status).inc()
    
    def record_api_request(self, pc_id: str, service_type: str, endpoint: str):
        """Record an API request"""
        self.api_requests.labels(pc_id=pc_id, service_type=service_type, endpoint=endpoint).inc()
    
    def record_error(self, pc_id: str, service_type: str, error_type: str):
        """Record a validation error"""
        self.validation_errors.labels(pc_id=pc_id, service_type=service_type, error_type=error_type).inc()
    
    def update_api_usage(self, pc_id: str, service_type: str, api_type: str, usage: float):
        """Update current API usage"""
        self.current_usage.labels(pc_id=pc_id, service_type=service_type, api_type=api_type).set(usage)
    
    def measure_time(self, pc_id: str, service_type: str):
        """Decorator to measure processing time"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.time()
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                finally:
                    duration = time.time() - start_time
                    self.processing_time.labels(pc_id=pc_id, service_type=service_type).observe(duration)
                return result
            return wrapper
        return decorator
    
    def update_system_metrics(self, pc_id: str):
        """Update system resource usage metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.system_metrics['cpu_usage'].labels(pc_id=pc_id).set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics['memory_usage'].labels(pc_id=pc_id).set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics['disk_usage'].labels(pc_id=pc_id).set(disk.percent)
        except Exception as e:
            print(f"Failed to update system metrics: {e}")

# Create a global metrics instance
metrics = MetricsCollector()

def start_metrics_server():
    """Start Prometheus metrics server"""
    try:
        metrics_port = Config.METRICS_PORT
        start_http_server(metrics_port)
        print(f"Started metrics server on port {metrics_port}")
    except Exception as e:
        print(f"Failed to start metrics server: {str(e)}")