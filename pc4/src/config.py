import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Config:
    # PC ID configuration
    PC_ID = os.getenv('PC_ID', 'PC4')
    
    # Service configuration
    SERVICE_TYPE = os.getenv('SERVICE_TYPE', 'leak_check')  # or 'domain_email'
    
    # RabbitMQ configuration
    RABBITMQ_CONFIG = {
        'host': os.getenv('RABBITMQ_HOST', 'localhost'),
        'port': int(os.getenv('RABBITMQ_PORT', 5672)),
        'user': os.getenv('RABBITMQ_USER', 'guest'),
        'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
        'queues': {
            'leak_check': 'leak_check_queue',
            'domain_email': 'domain_email_queue'
        }
    }

    # Logging configuration
    LOG_CONFIG = {
        'level': logging.INFO,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': logging.INFO,
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'logs/app.log',
                'level': logging.INFO,
            }
        }
    }

    # API configuration
    API_CONFIG = {
        'leak_check': {
            'base_url': os.getenv('LEAK_CHECK_API_URL', 'http://localhost:8000'),
            'timeout': int(os.getenv('API_TIMEOUT', 30))
        },
        'domain_email': {
            'base_url': os.getenv('DOMAIN_EMAIL_API_URL', 'http://localhost:8001'),
            'timeout': int(os.getenv('API_TIMEOUT', 30))
        }
    }

    # Redis configuration
    REDIS_CONFIG = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'password': os.getenv('REDIS_PASSWORD', None)
    }

    # Metrics configuration
    METRICS_PORT = int(os.getenv('METRICS_PORT', 8000))

    # API Keys configuration
    API_KEYS = {
        'dehashed': {
            'key': os.getenv('DEHASHED_API_KEY')
        },
        'leakcheck': {
            'key': os.getenv('LEAKCHECK_API_KEY')
        },
        'shodan': {
            'key': os.getenv('SHODAN_API_KEY')
        },
        'business': {
            'key': os.getenv('BUSINESS_API_KEY')
        },
        'outscraper': {
            'key': os.getenv('OUTSCRAPER_API_KEY')
        }
    }

    @classmethod
    def get_api_config(cls, service_type):
        return cls.API_CONFIG.get(service_type, {})