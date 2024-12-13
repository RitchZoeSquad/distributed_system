import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any

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
            self.logger.info(f"Making API request for business: {data.get('business_id', 'unknown')}")
            
            async with session.post(
                f"{self.base_url}/search",
                json=data,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Successfully retrieved data for business: {data.get('business_id', 'unknown')}")
                    return result
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
            self.logger.error(f"API request timed out for business: {data.get('business_id', 'unknown')}")
            raise
        except Exception as e:
            self.logger.error(f"API request failed for business {data.get('business_id', 'unknown')}: {str(e)}")
            raise

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None