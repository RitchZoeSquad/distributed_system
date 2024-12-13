class MonitoringConfig:
    # Existing configuration...

    # Add Shodan monitoring
    SHODAN_METRICS = {
        'search_requests': {
            'name': 'shodan_search_requests_total',
            'description': 'Total number of Shodan search requests',
            'labels': ['status']
        },
        'cache_hits': {
            'name': 'shodan_cache_hits_total',
            'description': 'Total number of Shodan cache hits'
        },
        'cache_misses': {
            'name': 'shodan_cache_misses_total',
            'description': 'Total number of Shodan cache misses'
        },
        'api_errors': {
            'name': 'shodan_api_errors_total',
            'description': 'Total number of Shodan API errors',
            'labels': ['error_type']
        }
    } 