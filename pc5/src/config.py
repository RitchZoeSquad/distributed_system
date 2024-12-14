import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Service configuration
    SERVICE_TYPE = os.getenv('SERVICE_TYPE', 'business')
    
    # RabbitMQ configuration
    RABBITMQ_CONFIG = {
        'host': os.getenv('RABBITMQ_HOST', 'localhost'),
        'port': int(os.getenv('RABBITMQ_PORT', 5672)),
        'user': os.getenv('RABBITMQ_USER', 'guest'),
        'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
        'queues': {
            'business': 'business_queue'
        }
    }

    # API configuration
    API_CONFIG = {
        'business': {
            'base_url': os.getenv('BUSINESS_API_URL', 'http://localhost:8000'),
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

    @classmethod
    def get_api_config(cls, service_type):
        return cls.API_CONFIG.get(service_type, {})