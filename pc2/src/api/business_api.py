import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any
import json

class BusinessAPI:
    def __init__(self):
        self.api_key = Config.BUSINESS_API_KEY
        self.logger = Logger('business_api')
        self.session = None
        self.base_url = "https://api.business.example.com/v1"  # Replace with actual API URL
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
        max_tries=3
    )
    async def search_business(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            session = await self.get_session()
            async with session.post(
                f"{self.base_url}/search",
                json=data,
                timeout=30
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    self.logger.error(f"API Error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(f"API Error: {response.status}")

        except asyncio.TimeoutError:
            self.logger.error("API request timed out")
            raise
        except Exception as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def search_businesses(self, occupation: str, city: str, state_code: str, max_retries: int = 3) -> Dict[str, Any]:
        """Search for businesses with retry logic"""
        url = "https://api.app.outscraper.com/maps/search-v3"
        
        for attempt in range(max_retries):
            params = {
                "query": f"{occupation}, {city}, {state_code}, USA",
                "limit": 10,
                "async": False,
                "filters": json.dumps([
                    {"key": "site", "operator": "is blank", "value": None},
                    {"key": "business_status", "operator": "not equal", "value": "CLOSED_PERMANENTLY"}
                ])
            }
            headers = {"X-API-KEY": self.api_key}
            
            try:
                async with self.session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'data' in result:
                            active_businesses = [
                                business for business in result['data']
                                if isinstance(business, list) and business 
                                and isinstance(business[0], dict)
                                and business[0].get('business_status') != 'CLOSED_PERMANENTLY'
                            ][:3]
                            
                            if active_businesses:
                                return {"data": active_businesses}
                
                    # Expand search radius if no results
                    params["query"] = f"{occupation}, {state_code}, USA"
                
            except Exception as e:
                self.logger.error(f"Search attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(2)
                continue
            
            await asyncio.sleep(2)
        
        return None