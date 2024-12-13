import redis
from datetime import datetime, timedelta
from config import Config
from utils.logger import Logger
import asyncio
from typing import Optional
import backoff

class RateLimiter:
    def __init__(self):
        self.redis = redis.Redis(
            host='185.249.196.192',
            port=6379,
            password='TestingPurposes9!',
            db=0,
            decode_responses=True
        )
        self.logger = Logger('rate_limiter')
        self.daily_limit = Config.DAILY_LIMIT
        self.lock_timeout = 300  # 5 minutes

    @backoff.on_exception(
        backoff.expo,
        redis.RedisError,
        max_tries=3
    )
    async def can_make_request(self) -> bool:
        """Check if we can make a request based on daily limit"""
        try:
            key = f"api_usage:{Config.PC_ID}:{datetime.now().strftime('%Y-%m-%d')}"
            current_usage = int(self.redis.get(key) or 0)
            can_proceed = current_usage < self.daily_limit
            
            if not can_proceed:
                self.logger.warning(f"SERP rate limit reached: {current_usage}/{self.daily_limit}")
            
            return can_proceed
        except redis.RedisError as e:
            self.logger.error(f"Redis error in can_make_request: {str(e)}")
            return False

    async def increment_usage(self) -> int:
        """Increment the usage counter and return new value"""
        key = f"api_usage:{Config.PC_ID}:{datetime.now().strftime('%Y-%m-%d')}"
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expireat(
                key,
                (datetime.now() + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            )
            result = pipe.execute()
            
            current_usage = result[0]
            self.logger.debug(f"Current SERP API usage: {current_usage}/{self.daily_limit}")
            
            return current_usage
        except redis.RedisError as e:
            self.logger.error(f"Redis error in increment_usage: {str(e)}")
            raise

    async def get_current_usage(self) -> int:
        """Get current API usage count"""
        try:
            key = f"api_usage:{Config.PC_ID}:{datetime.now().strftime('%Y-%m-%d')}"
            return int(self.redis.get(key) or 0)
        except redis.RedisError as e:
            self.logger.error(f"Redis error in get_current_usage: {str(e)}")
            return 0

    async def cache_result(self, query: str, result: dict, ttl: int = 3600) -> bool:
        """Cache SERP result"""
        key = f"serp_cache:{query}"
        try:
            return self.redis.setex(
                key,
                ttl,
                json.dumps(result)
            )
        except redis.RedisError as e:
            self.logger.error(f"Redis error in cache_result: {str(e)}")
            return False

    async def get_cached_result(self, query: str) -> Optional[dict]:
        """Get cached SERP result"""
        key = f"serp_cache:{query}"
        try:
            result = self.redis.get(key)
            if result:
                return json.loads(result)
            return None
        except redis.RedisError as e:
            self.logger.error(f"Redis error in get_cached_result: {str(e)}")
            return None