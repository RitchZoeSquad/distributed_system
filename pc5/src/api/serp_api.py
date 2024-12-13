import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any, List
import time

class SerpAPI:
    def __init__(self):
        self.api_key = "d52cf65f-ccac-41a4-93b1-f54d0b8b1190"  # SpaceSerp API key
        self.logger = Logger('serp_api')
        self.session = None
        self.base_url = "https://api.spaceserp.com/google/search"

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"SerpWorker-{Config.PC_ID}"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def search(self, query: str, location: str = None, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            session = await self.get_session()
            params = {
                'apiKey': self.api_key,
                'q': query,
                'location': location,
                'domain': 'google.com',
                'gl': 'us',
                'hl': 'en',
                'resultFormat': 'json',
                'device': 'desktop',
                'pageSize': 10,
                'pageNumber': 1,
                **(parameters or {})
            }

            self.logger.info(f"Making SERP API request for query: {query}")
            
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Successfully retrieved SERP results for: {query}")
                    return result
                    
                elif response.status == 429:  # Rate limit exceeded
                    self.logger.warning(f"SERP API rate limit exceeded, waiting 2 seconds")
                    await asyncio.sleep(2)
                    raise aiohttp.ClientError("Rate limit exceeded")
                    
                else:
                    error_text = await response.text()
                    self.logger.error(f"SERP API Error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(f"SERP API Error: {response.status}")

        except asyncio.TimeoutError:
            self.logger.error(f"SERP API request timeout for query: {query}")
            raise
        except Exception as e:
            self.logger.error(f"SERP API request failed for query {query}: {str(e)}")
            raise

    async def search_business(self, business_data: Dict[str, Any], city: str, state_code: str) -> Dict[str, Any]:
        """Search SERP specifically for a business"""
        try:
            # Safely get business details
            business_name = business_data.get('name', '')
            business_address = business_data.get('full_address', '')
            
            if not business_name:
                self.logger.warning("No business name provided for SERP search")
                return None
            
            # Create a specific search query for the business
            search_query = f'"{business_name}" {city} {state_code}'
            
            # Get SERP results for this specific business
            serp_results = await self.search(
                query=search_query,
                location=f"{city},{state_code},USA",
                parameters={'pageSize': 5}
            )
            
            return {
                'business_name': business_name,
                'business_address': business_address,
                'serp_results': serp_results
            }

        except Exception as e:
            self.logger.error(f"Error in search_business: {str(e)}")
            raise

    async def batch_search_businesses(self, businesses: List[Dict[str, Any]], city: str, state_code: str) -> List[Dict[str, Any]]:
        """Perform batch SERP searches for multiple businesses"""
        results = []
        for business in businesses:
            try:
                result = await self.search_business(business, city, state_code)
                if result:
                    results.append(result)
                await asyncio.sleep(1)  # Rate limiting delay
            except Exception as e:
                self.logger.error(f"Error processing business in batch: {str(e)}")
                continue
        return results

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def search_business_profile(self, business_data: Dict[str, Any], city: str, state_code: str) -> Dict[str, Any]:
        """Search SERP for a specific business profile"""
        try:
            # Extract business info
            business = business_data[0] if isinstance(business_data, list) else business_data
            
            business_name = business.get('name', '')
            business_address = business.get('full_address', '')
            
            if not business_name:
                self.logger.warning("No business name provided for SERP search")
                return None
            
            # Create specific search query
            search_query = f'"{business_name}" {city} {state_code}'
            
            # Check cache first
            cached_result = await self.rate_limiter.get_cached_result(search_query)
            if cached_result:
                self.metrics.increment_cache_hit()
                return cached_result
            
            self.metrics.increment_cache_miss()
            
            # Get fresh SERP results
            serp_results = await self.search(
                query=search_query,
                location=f"{city},{state_code},USA",
                parameters={'pageSize': 5}
            )
            
            # Cache the results
            await self.rate_limiter.cache_result(search_query, serp_results)
            
            return {
                'business_name': business_name,
                'business_address': business_address,
                'serp_results': serp_results
            }

        except Exception as e:
            self.logger.error(f"Error in search_business_profile: {str(e)}")
            raise