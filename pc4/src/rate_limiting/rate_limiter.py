import redis
from datetime import datetime, timedelta
from config import Config
from utils.logger import Logger
import asyncio
from typing import Optional, Dict
import backoff

class RateLimiter:
    def __init__(self):
        self.redis = redis.Redis(
            decode_responses=True,
            **Config.REDIS_CONFIG
        ) 