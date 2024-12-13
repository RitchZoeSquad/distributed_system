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
            'phone': 'phone_queue'
        }
    }
    
    # API Configuration
    API_KEYS = {
        'domain': {
            'key': 'ta_5xbwm66o5844vy6mqdpecnplz83wyhcq6uwaz',
            'secret': 'ts_27bd86ee-7947-46f5-b695-5f32a217be2e'
        },
        'email': {
            'key': 'ta_5xbwm66o5844vy6mqdpecnplz83wyhcq6uwaz',
            'secret': 'ts_27bd86ee-7947-46f5-b695-5f32a217be2e'
        }
    }
    
    # API Limits
    DAILY_LIMITS = {
        'domain_email': 333,  # Combined domain/email validation limit
        'phone': 16          # Phone validation limit
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