from prometheus_client import Counter, Gauge, Histogram

# Leak Check API Metrics
leak_check_requests = Counter(
    'leak_check_requests_total',
    'Total number of leak check requests',
    ['api_type']  # 'dehashed' or 'leakcheck'
)

leak_check_errors = Counter(
    'leak_check_errors_total',
    'Total number of leak check errors',
    ['api_type', 'error_type']
)

leak_check_latency = Histogram(
    'leak_check_request_duration_seconds',
    'Leak check request duration in seconds',
    ['api_type']
)

leak_check_rate_limit = Gauge(
    'leak_check_rate_limit_remaining',
    'Remaining rate limit for leak check APIs',
    ['api_type']
)

# Cache Metrics
cache_hits = Counter(
    'leak_check_cache_hits_total',
    'Total number of cache hits'
)

cache_misses = Counter(
    'leak_check_cache_misses_total',
    'Total number of cache misses'
)

# Result Metrics
leaks_found = Counter(
    'leak_check_leaks_found_total',
    'Total number of leaks found',
    ['severity']
)

password_leaks = Counter(
    'leak_check_password_leaks_total',
    'Total number of password leaks found'
)

# Add Shodan metrics
shodan_requests = Counter(
    'shodan_requests_total',
    'Total number of Shodan API requests',
    ['endpoint', 'status']
)

shodan_errors = Counter(
    'shodan_errors_total',
    'Total number of Shodan API errors',
    ['endpoint', 'error']
)

shodan_latency = Histogram(
    'shodan_request_duration_seconds',
    'Shodan API request duration in seconds'
) 