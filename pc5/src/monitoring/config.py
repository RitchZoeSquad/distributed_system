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

    API_METRICS = {
        'shodan': {
            'requests_total': 'Counter',
            'errors_total': 'Counter',
            'request_duration_seconds': 'Histogram'
        },
        'leakcheck': {
            'requests_total': 'Counter',
            'errors_total': 'Counter',
            'request_duration_seconds': 'Histogram'
        },
        'dehashed': {
            'requests_total': 'Counter',
            'errors_total': 'Counter',
            'request_duration_seconds': 'Histogram'
        },
        'serp': {
            'requests_total': 'Counter',
            'errors_total': 'Counter',
            'request_duration_seconds': 'Histogram'
        },
        'outscraper': {
            'requests_total': 'Counter',
            'errors_total': 'Counter',
            'request_duration_seconds': 'Histogram'
        }
    } 