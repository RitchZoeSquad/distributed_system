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
        self.processed_queries = Counter(
            'serp_queries_processed_total',
            'Total number of SERP queries processed',
            ['pc_id', 'status']
        )
        
        self.api_requests = Counter(
            'serp_api_requests_total',
            'Total number of SERP API requests made',
            ['pc_id', 'endpoint']
        )
        
        self.api_errors = Counter(
            'serp_api_errors_total',
            'Total number of SERP API errors',
            ['pc_id', 'error_type']
        )
        
        self.current_usage = Gauge(
            'serp_current_usage',
            'Current SERP API usage count',
            ['pc_id']
        )
        
        self.processing_time = Histogram(
            'serp_processing_seconds',
            'Time spent processing SERP queries',
            ['pc_id'],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30)
        )
        
        self.query_results = Histogram(
            'serp_results_count',
            'Number of results per SERP query',
            ['pc_id'],
            buckets=(1, 5, 10, 20, 50, 100)
        )
        
        self.cache_hits = Counter(
            'serp_cache_hits_total',
            'Total number of SERP cache hits',
            ['pc_id']
        )
        
        self.cache_misses = Counter(
            'serp_cache_misses_total',
            'Total number of SERP cache misses',
            ['pc_id']
        )

        # System metrics
        self.memory_usage = Gauge(
            'serp_memory_usage_bytes',
            'Current memory usage',
            ['pc_id', 'type']
        )
        
        self.cpu_usage = Gauge(
            'serp_cpu_usage_percent',
            'Current CPU usage percentage',
            ['pc_id']
        )
        
        # Queue metrics
        self.queue_size = Gauge(
            'serp_queue_size',
            'Current size of the SERP queue',
            ['pc_id']
        )

        # Start metrics server
        start_http_server(8000)

    def increment_processed_queries(self, status: str = 'success'):
        """Increment the processed queries counter"""
        self.processed_queries.labels(
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
        """Record the processing time"""
        self.processing_time.labels(
            pc_id=Config.PC_ID
        ).observe(time.time() - start_time)

    def record_result_count(self, count: int):
        """Record the number of results for a query"""
        self.query_results.labels(
            pc_id=Config.PC_ID
        ).observe(count)

    def increment_cache_hit(self):
        """Increment cache hit counter"""
        self.cache_hits.labels(
            pc_id=Config.PC_ID
        ).inc()

    def increment_cache_miss(self):
        """Increment cache miss counter"""
        self.cache_misses.labels(
            pc_id=Config.PC_ID
        ).inc()

    def time(self) -> float:
        """Get current time for timing operations"""
        return time.time()

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
                
                # Queue size metrics
                # This would need to be implemented based on your queue system
                # self.update_queue_size()
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                self.increment_api_errors(f"metrics_collection_{type(e).__name__}")
                await asyncio.sleep(60)

    def update_queue_size(self, size: int):
        """Update the queue size metric"""
        self.queue_size.labels(
            pc_id=Config.PC_ID
        ).set(size)