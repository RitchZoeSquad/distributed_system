from prometheus_client import Counter, Histogram

# SERP API metrics
serp_requests = Counter(
    'serp_api_requests_total',
    'Total number of SERP API requests',
    ['status']
)

serp_errors = Counter(
    'serp_api_errors_total',
    'Total number of SERP API errors',
    ['error']
)

serp_latency = Histogram(
    'serp_api_request_duration_seconds',
    'SERP API request duration in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
) 