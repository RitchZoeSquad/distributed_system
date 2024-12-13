import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any, List
from monitoring.metrics import serp_requests, serp_errors, serp_latency

class SerpAPI:
    def __init__(self):
        self.api_key = Config.API_KEYS['serp']['key']  # d52cf65f-ccac-41a4-93b1-f54d0b8b1190
        self.base_url = "https://api.spaceserp.com/google/search"
        self.logger = Logger('serp_api')
        self.session = None

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"SerpWorker-{Config.PC_ID}"
                }
            )
        return self.session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def search(self, query: str, location: str = None) -> Dict[str, Any]:
        """
        Search using SpaceSerp API
        
        Args:
            query: Search query
            location: Optional location parameter
        """
        try:
            with serp_latency.time():
                session = await self.get_session()
                params = {
                    'apiKey': self.api_key,
                    'q': query,
                    'domain': 'google.com',
                    'gl': 'us',  # Country (United States)
                    'hl': 'en',  # Language (English)
                    'device': 'desktop',
                    'page': '1',
                }

                if location:
                    params['location'] = location

                self.logger.info(f"Making SERP API request for query: {query}")
                
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        serp_requests.labels(status='success').inc()
                        result = await response.json()
                        return {
                            'organic_results': result.get('organic_results', []),
                            'shopping_results': result.get('shopping_carousel', []),
                            'ads': result.get('ads_results', []),
                            'query': query,
                            'location': location
                        }
                    else:
                        serp_errors.labels(error=str(response.status)).inc()
                        error_text = await response.text()
                        self.logger.error(f"SERP API Error: {response.status} - {error_text}")
                        return None

        except Exception as e:
            serp_errors.labels(error=str(type(e).__name__)).inc()
            self.logger.error(f"SERP API request failed: {str(e)}")
            raise

    async def search_business(self, business_name: str, city: str, state: str) -> Dict[str, Any]:
        """Search specifically for a business"""
        query = f"{business_name} {city} {state}"
        location = f"{city}, {state}, USA"
        return await self.search(query, location)

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None