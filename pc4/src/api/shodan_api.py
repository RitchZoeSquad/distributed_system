import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from config import Config
from utils.logger import Logger
from monitoring.metrics import shodan_requests, shodan_errors, shodan_latency
import backoff
import json

class ShodanAPI:
    def __init__(self):
        self.api_key = Config.API_KEYS['shodan']['key']
        self.base_url = "https://api.shodan.io"
        self.logger = Logger('shodan_api')
        self.session = None
        self.excluded_domains = [
            "www.yelp.com",
            "www.facebook.com",
            "www.instagram.com",
            "www.youtube.com"
        ]

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"ShodanWorker-{Config.PC_ID}"
                }
            )
        return self.session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def search_host(self, query: str) -> List[Dict]:
        """Search Shodan using raw HTTP requests"""
        try:
            with shodan_latency.time():
                session = await self.get_session()
                params = {
                    'key': self.api_key,
                    'query': query
                }
                
                url = f"{self.base_url}/shodan/host/search"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        shodan_requests.labels(endpoint='search', status='success').inc()
                        data = await response.json()
                        
                        filtered_results = []
                        for result in data.get('matches', []):
                            # Skip excluded domains
                            hostnames = result.get('hostnames', [])
                            if any(domain in hostnames for domain in self.excluded_domains):
                                continue

                            # Format result similar to your original code
                            result_str = {
                                'ip': result.get('ip_str'),
                                'port': result.get('port'),
                                'organization': result.get('org'),
                                'hostnames': hostnames,
                                'raw_data': result  # Keep raw data for additional processing
                            }
                            filtered_results.append(result_str)

                        return filtered_results
                    else:
                        shodan_errors.labels(endpoint='search', error=str(response.status)).inc()
                        self.logger.error(f"Shodan API error: {response.status}")
                        return []

        except Exception as e:
            shodan_errors.labels(endpoint='search', error=str(type(e).__name__)).inc()
            self.logger.error(f"Error in host search: {str(e)}")
            raise

    async def get_host_info(self, ip: str) -> Dict:
        """Get host information using raw HTTP request"""
        try:
            with shodan_latency.time():
                session = await self.get_session()
                params = {'key': self.api_key}
                
                url = f"{self.base_url}/shodan/host/{ip}"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        shodan_requests.labels(endpoint='host_info', status='success').inc()
                        return await response.json()
                    else:
                        shodan_errors.labels(endpoint='host_info', error=str(response.status)).inc()
                        self.logger.error(f"Error getting host info: {response.status}")
                        return None

        except Exception as e:
            shodan_errors.labels(endpoint='host_info', error=str(type(e).__name__)).inc()
            self.logger.error(f"Error getting host info: {str(e)}")
            raise

    async def write_results_to_file(self, results: List[Dict], output_file: str):
        """Write results to file similar to your original code"""
        try:
            with open(output_file, 'a') as file:
                for result in results:
                    result_str = (
                        f"IP: {result['ip']}\n"
                        f"Port: {result['port']}\n"
                        f"Organization: {result['organization']}\n"
                        f"Hostnames: {', '.join(result['hostnames'])}\n"
                        + "-"*40 + "\n"
                    )
                    file.write(result_str)
        except Exception as e:
            self.logger.error(f"Error writing to file: {str(e)}")
            raise

    async def write_to_database(self, results: List[Dict], cur, conn):
        """Write results to database similar to your original code"""
        try:
            for result in results:
                cur.execute("""
                    INSERT INTO shodan_searches 
                    (search_query, ip_address, port, organization, hostnames, additional_info)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    result.get('query', ''),
                    result['ip'],
                    result['port'],
                    result['organization'],
                    json.dumps(result['hostnames']),
                    json.dumps(result['raw_data'])
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()