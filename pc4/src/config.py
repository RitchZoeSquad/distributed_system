import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PC Identification
    PC_ID = "PC4"
    
    # Central Services (PC1) Configuration
    PC1_IP = os.getenv('PC1_IP')
    
    # Database Configuration
    DB_CONFIG = {
        'host': PC1_IP,
        'port': 5432,
        'database': 'business_db',
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD')
    }
    
    # Redis Configuration
    REDIS_CONFIG = {
        'host': PC1_IP,
        'port': 6379,
        'password': os.getenv('REDIS_PASSWORD'),
        'db': 0
    }
    
    # RabbitMQ Configuration
    RABBITMQ_CONFIG = {
        'host': PC1_IP,
        'port': 5672,
        'user': os.getenv('RABBITMQ_USER'),
        'password': os.getenv('RABBITMQ_PASS'),
        'queues': {
            'domain_email': 'domain_email_queue',
            'phone': 'phone_queue',
            'leak_check': 'leak_check_queue'
        }
    }
    
    # API Configuration
    API_KEYS = {
        'domain': {
            'key': 'ta_5xbwm66o5844vy6mqdpecnplz83wyhcq6uwaz',
            'secret': 'ts_27bd86ee-7947-46f5-b695-5f32a217be2e'
        },
        'dehashed': {
            'key': os.getenv('DEHASHED_API_KEY')
        },
        'leakcheck': {
            'key': os.getenv('LEAKCHECK_API_KEY')
        },
        'shodan': {
            'key': os.getenv('SHODAN_API_KEY')
        }
    }
    
    # API Limits
    DAILY_LIMITS = {
        'domain_email': 333,  # Combined domain/email validation limit
        'phone': 16,         # Phone validation limit
        'leak_check': {
            'dehashed': 200,  # 200 checks per day
            'leakcheck': 200  # 200 checks per day
        }
    }
    
    # API Endpoints
    API_ENDPOINTS = {
        'domain': 'https://api.domain-validator.example.com/v1',
        'email': 'https://api.email-validator.example.com/v1',
        'phone': 'https://api.phone-validator.example.com/v1'
    }
    
    # Health Check Configuration
    HEALTH_CHECK_PORT = 8000
    
    # Logging Configuration
    LOG_CONFIG = {
        'filename': f'/app/logs/pc4_{PC_ID}.log',
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }

    # Retry Configuration
    RETRY_CONFIG = {
        'max_retries': 3,
        'initial_delay': 1,
        'max_delay': 10,
        'exponential_base': 2
    }

    # Batch Processing Configuration
    BATCH_CONFIG = {
        'domain_email_batch_size': 50,
        'phone_batch_size': 10,
        'max_batch_window': 60  # seconds
    }

    # Add Shodan rate limits
    RATE_LIMITS = {
        'shodan': {
            'host_lookup': 1,  # requests per second
            'search': 1,       # requests per second
            'scan': 1         # requests per minute
        }
    }

    # Service-specific configurations
    SERVICES = {
        'domain_email': {
            'port': 8000,
            'queue': 'domain_email_queue'
        },
        'leak_check': {
            'port': 8001,
            'queue': 'leak_check_queue'
        },
        'shodan': {
            'port': 8002,
            'queue': 'shodan_search_queue',
            'host_queue': 'shodan_host_queue'
        }
    }

    # Shodan-specific configuration
    SHODAN_CONFIG = {
        'rate_limit': {
            'searches_per_second': 1,
            'scans_per_minute': 1
        },
        'excluded_domains': [
            "www.yelp.com",
            "www.facebook.com",
            "www.instagram.com",
            "www.youtube.com"
        ]
    }