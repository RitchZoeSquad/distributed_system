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
        self.logger = Logger('rate_limiter')
        self.daily_limits = Config.DAILY_LIMITS
        self.lock_timeout = 300  # 5 minutes

    async def can_make_request(self, service_type: str) -> bool:
        """Check if we can make a request based on daily limit"""
        try:
            key = f"api_usage:{Config.PC_ID}:{service_type}:{datetime.now().strftime('%Y-%m-%d')}"
            current_usage = int(self.redis.get(key) or 0)
            limit = self.daily_limits[service_type]
            can_proceed = current_usage < limit
            
            if not can_proceed:
                self.logger.warning(f"{service_type} rate limit reached: {current_usage}/{limit}")
            
            return can_proceed
        except redis.RedisError as e:
            self.logger.error(f"Redis error in can_make_request for {service_type}: {str(e)}")
            return False

    @backoff.on_exception(
        backoff.expo,
        redis.RedisError,
        max_tries=3
    )
    async def increment_usage(self, service_type: str) -> int:
        """Increment the usage counter and return new value"""
        key = f"api_usage:{Config.PC_ID}:{service_type}:{datetime.now().strftime('%Y-%m-%d')}"
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
            
            self.logger.debug(
                f"Current {service_type} API usage: {current_usage}/{self.daily_limits[service_type]}"
            )
            
            return current_usage
        except redis.RedisError as e:
            self.logger.error(f"Redis error in increment_usage for {service_type}: {str(e)}")
            raise

    async def acquire_lock(self, resource_id: str, service_type: str, timeout: int = 30) -> bool:
        """Acquire a distributed lock"""
        lock_key = f"lock:{Config.PC_ID}:{service_type}:{resource_id}"
        lock_value = datetime.now().isoformat()
        
        try:
            acquired = self.redis.set(
                lock_key,
                lock_value,
                ex=timeout,
                nx=True
            )
            if acquired:
                self.logger.debug(f"Acquired {service_type} lock for resource: {resource_id}")
            return bool(acquired)
        except redis.RedisError as e:
            self.logger.error(f"Redis error in acquire_lock for {service_type}: {str(e)}")
            return False

    async def release_lock(self, resource_id: str, service_type: str) -> bool:
        """Release a distributed lock"""
        lock_key = f"lock:{Config.PC_ID}:{service_type}:{resource_id}"
        try:
            released = bool(self.redis.delete(lock_key))
            if released:
                self.logger.debug(f"Released {service_type} lock for resource: {resource_id}")
            return released
        except redis.RedisError as e:
            self.logger.error(f"Redis error in release_lock for {service_type}: {str(e)}")
            return False

    async def get_current_usage(self, service_type: str) -> int:
        """Get current API usage count"""
        try:
            key = f"api_usage:{Config.PC_ID}:{service_type}:{datetime.now().strftime('%Y-%m-%d')}"
            return int(self.redis.get(key) or 0)
        except redis.RedisError as e:
            self.logger.error(f"Redis error in get_current_usage for {service_type}: {str(e)}")
            return 0

    async def get_all_usage(self) -> Dict[str, int]:
        """Get current usage for all services"""
        usage = {}
        for service_type in self.daily_limits.keys():
            usage[service_type] = await self.get_current_usage(service_type)
        return usage

    async def check_rate_limit(self, service_type: str, key: str, limit: int, window: int = 60) -> bool:
        """Check rate limit using sliding window"""
        window_key = f"ratelimit:{Config.PC_ID}:{service_type}:{key}:{window}"
        now = datetime.now().timestamp()
        window_start = now - window
        
        try:
            pipe = self.redis.pipeline()
            # Remove old entries
            pipe.zremrangebyscore(window_key, '-inf', window_start)
            # Count requests in current window
            pipe.zcard(window_key)
            # Add new request
            pipe.zadd(window_key, {str(now): now})
            # Set expiry on the key
            pipe.expire(window_key, window * 2)
            
            _, current_count, _, _ = pipe.execute()
            return current_count < limit
        except redis.RedisError as e:
            self.logger.error(f"Redis error in check_rate_limit for {service_type}: {str(e)}")
            return False