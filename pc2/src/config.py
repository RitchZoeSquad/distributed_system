import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PC Identification
    PC_ID = "PC2"
    
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
        'exchange_name': 'business_events',
        'queue_name': 'business_queue'
    }
    
    # API Configuration
    API_CONFIG = {
        'base_url': f'http://{PC1_IP}:8000',
        'api_key': os.getenv('BUSINESS_API_KEY')
    }
    
    # Outscraper Configuration
    OUTSCRAPER_CONFIG = {
        'api_key': os.getenv('OUTSCRAPER_API_KEY')
    }
    
    # Health Check Configuration
    HEALTH_CHECK_PORT = 8000
    
    # Logging Configuration
    LOG_CONFIG = {
        'filename': f'/app/logs/pc2_{PC_ID}.log',
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