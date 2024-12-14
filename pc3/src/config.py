import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PC Identification
    PC_ID = os.getenv('PC_ID', 'PC3')
    
    # Central Services (PC1) Configuration
    PC1_IP = os.getenv('PC1_IP', 'localhost')
    
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
        'url': f"amqp://{os.getenv('RABBITMQ_USER')}:{os.getenv('RABBITMQ_PASS')}@{PC1_IP}:5672/",
        'exchange_name': 'business_exchange',
        'queue_name': f"business_queue_{PC_ID}",
        'routing_key': 'business.*'
    }

    # API Configuration
    API_CONFIG = {
        'base_url': f"http://{PC1_IP}:8000/api",
        'api_key': os.getenv('BUSINESS_API_KEY'),
        'timeout': 30
    }

    # Outscraper Configuration
    OUTSCRAPER_CONFIG = {
        'api_key': os.getenv('OUTSCRAPER_API_KEY')
    }

    # Health Check Configuration
    HEALTH_CHECK_PORT = 8000
    
    # Logging Configuration
    LOG_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'directory': 'logs'
    }

    # Retry Configuration
    RETRY_CONFIG = {
        'max_retries': 5,
        'max_time': 30,
        'initial_delay': 1,
        'backoff_factor': 2
    }