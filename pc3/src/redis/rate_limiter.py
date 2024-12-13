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
            decode_responses=True,
            **Config.REDIS_CONFIG
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
                self.logger.warning(f"Rate limit reached: {current_usage}/{self.daily_limit}")
            
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
            self.logger.debug(f"Current API usage: {current_usage}/{self.daily_limit}")
            
            return current_usage
        except redis.RedisError as e:
            self.logger.error(f"Redis error in increment_usage: {str(e)}")
            raise

    async def acquire_lock(self, resource_id: str, timeout: int = 30) -> bool:
        """Acquire a distributed lock"""
        lock_key = f"lock:{Config.PC_ID}:{resource_id}"
        lock_value = datetime.now().isoformat()
        
        try:
            acquired = self.redis.set(
                lock_key,
                lock_value,
                ex=timeout,
                nx=True
            )
            if acquired:
                self.logger.debug(f"Acquired lock for resource: {resource_id}")
            return bool(acquired)
        except redis.RedisError as e:
            self.logger.error(f"Redis error in acquire_lock: {str(e)}")
            return False

    async def release_lock(self, resource_id: str) -> bool:
        """Release a distributed lock"""
        lock_key = f"lock:{Config.PC_ID}:{resource_id}"
        try:
            released = bool(self.redis.delete(lock_key))
            if released:
                self.logger.debug(f"Released lock for resource: {resource_id}")
            return released
        except redis.RedisError as e:
            self.logger.error(f"Redis error in release_lock: {str(e)}")
            return False

    async def get_current_usage(self) -> int:
        """Get current API usage count"""
        try:
            key = f"api_usage:{Config.PC_ID}:{datetime.now().strftime('%Y-%m-%d')}"
            return int(self.redis.get(key) or 0)
        except redis.RedisError as e:
            self.logger.error(f"Redis error in get_current_usage: {str(e)}")
            return 0

    async def check_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """Check rate limit using sliding window"""
        now = datetime.now().timestamp()
        window_start = now - window
        
        try:
            pipe = self.redis.pipeline()
            # Remove old entries
            pipe.zremrangebyscore(key, '-inf', window_start)
            # Count requests in current window
            pipe.zcard(key)
            # Add new request
            pipe.zadd(key, {str(now): now})
            # Set expiry on the key
            pipe.expire(key, window * 2)
            
            _, current_count, _, _ = pipe.execute()
            return current_count < limit
        except redis.RedisError as e:
            self.logger.error(f"Redis error in check_rate_limit: {str(e)}")
            return False