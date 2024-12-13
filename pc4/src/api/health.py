from fastapi import APIRouter, Response
from typing import Dict
import psutil
import aioredis
import aio_pika
from config import Config

router = APIRouter()

@router.get("/health/shodan")
async def shodan_health() -> Dict:
    """Check health of Shodan service components"""
    health_status = {
        "status": "healthy",
        "components": {
            "redis": "healthy",
            "rabbitmq": "healthy",
            "postgres": "healthy",
            "api": "healthy"
        },
        "metrics": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }
    }

    try:
        # Check Redis
        redis = aioredis.from_url(
            f"redis://{Config.REDIS_CONFIG['host']}:{Config.REDIS_CONFIG['port']}"
        )
        await redis.ping()
        await redis.close()
    except Exception as e:
        health_status["components"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"

    try:
        # Check RabbitMQ
        connection = await aio_pika.connect_robust(
            f"amqp://{Config.RABBITMQ_CONFIG['user']}:{Config.RABBITMQ_CONFIG['password']}"
            f"@{Config.RABBITMQ_CONFIG['host']}:{Config.RABBITMQ_CONFIG['port']}/"
        )
        await connection.close()
    except Exception as e:
        health_status["components"]["rabbitmq"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status 