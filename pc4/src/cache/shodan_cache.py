import json
from typing import Optional, Dict, Any
import aioredis
from config import Config
from utils.logger import Logger

class ShodanCache:
    def __init__(self):
        self.redis = aioredis.from_url(
            f"redis://{Config.REDIS_CONFIG['host']}:{Config.REDIS_CONFIG['port']}",
            password=Config.REDIS_CONFIG['password'],
            db=Config.REDIS_CONFIG['db']
        )
        self.logger = Logger('shodan_cache')
        self.ttl = 3600 * 24  # Cache for 24 hours

    async def get_search_results(self, query: str) -> Optional[Dict]:
        """Get cached search results"""
        try:
            cached = await self.redis.get(f"shodan:search:{query}")
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {str(e)}")
            return None

    async def set_search_results(self, query: str, results: Dict[str, Any]):
        """Cache search results"""
        try:
            await self.redis.setex(
                f"shodan:search:{query}",
                self.ttl,
                json.dumps(results)
            )
        except Exception as e:
            self.logger.error(f"Redis set error: {str(e)}")

    async def get_host_info(self, ip: str) -> Optional[Dict]:
        """Get cached host information"""
        try:
            cached = await self.redis.get(f"shodan:host:{ip}")
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            self.logger.error(f"Redis get error: {str(e)}")
            return None

    async def set_host_info(self, ip: str, info: Dict[str, Any]):
        """Cache host information"""
        try:
            await self.redis.setex(
                f"shodan:host:{ip}",
                self.ttl,
                json.dumps(info)
            )
        except Exception as e:
            self.logger.error(f"Redis set error: {str(e)}")

    async def close(self):
        """Close Redis connection"""
        await self.redis.close() 