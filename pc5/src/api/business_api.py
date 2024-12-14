import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any
import json

class BusinessAPI:
    def __init__(self):
        self.api_key = Config.API_CONFIG['api_key']
        self.logger = Logger('business_api')
        self.session = None
        self.base_url = Config.API_CONFIG['base_url']
        self.retry_config = Config.RETRY_CONFIG

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": f"BusinessWorker-{Config.PC_ID}"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        max_time=30
    )
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Business API with retries"""
        session = await self.get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            self.logger.info(f"Making {method} request to {url}")
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_business(self, business_id: str) -> Dict[str, Any]:
        """Get business details by ID"""
        return await self.make_request('GET', f'/business/{business_id}')

    async def create_business(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new business"""
        return await self.make_request('POST', '/business', json=business_data)

    async def update_business(self, business_id: str, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing business"""
        return await self.make_request('PUT', f'/business/{business_id}', json=business_data)

    async def delete_business(self, business_id: str) -> Dict[str, Any]:
        """Delete a business"""
        return await self.make_request('DELETE', f'/business/{business_id}')

    async def search_businesses(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search for businesses"""
        return await self.make_request('POST', '/business/search', json=query)

    async def get_business_stats(self) -> Dict[str, Any]:
        """Get business statistics"""
        return await self.make_request('GET', '/business/stats')
