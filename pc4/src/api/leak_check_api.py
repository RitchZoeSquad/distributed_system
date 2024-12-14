import requests
from leakcheck import LeakCheckAPI_v2
from config import Config
from utils.logger import Logger
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio
import aiohttp
import backoff
from rate_limiting import RateLimiter
from datetime import datetime
import json
import hashlib
import re

class SearchType(Enum):
    AUTO = 'auto'
    EMAIL = 'email'
    DOMAIN = 'domain'
    KEYWORD = 'keyword'
    USERNAME = 'username'
    PHONE = 'phone'
    HASH = 'hash'
    PHASH = 'phash'
    ORIGIN = 'origin'
    PASSWORD = 'password'

class DehashedSearchType(Enum):
    EMAIL = 'email'
    USERNAME = 'username'
    IP_ADDRESS = 'ip_address'
    NAME = 'name'
    ADDRESS = 'address'
    PHONE = 'phone'
    VIN = 'vin'
    FREE = 'free'

class ExperimentalSearchType(Enum):
    USERNAME = 'username'
    MASS = 'mass'
    EMAIL = 'email'
    LASTIP = 'lastip'
    PASSWORD = 'password'
    NAME = 'name'
    HASH = 'hash'

class LeakCheckError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class LeakCheckAPI:
    def __init__(self):
        self.logger = Logger('leak_check_api')
        self.dehashed_key = Config.API_KEYS['dehashed']['key']
        self.leakcheck_key = Config.API_KEYS['leakcheck']['key']
        self.session = None
        self.rate_limiter = RateLimiter()

    def _validate_query(self, query: str, search_type: SearchType) -> bool:
        """Validate query based on search type"""
        if len(query) < 3:
            raise LeakCheckError("Query too short (minimum 3 characters)", 400)

        if search_type == SearchType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, query):
                raise LeakCheckError("Invalid email format", 400)
        
        elif search_type == SearchType.DOMAIN:
            domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
            if not re.match(domain_pattern, query):
                raise LeakCheckError("Invalid domain format", 400)
        
        elif search_type == SearchType.PHONE:
            phone_pattern = r'^\+?[\d\s-]{10,}$'
            if not re.match(phone_pattern, query):
                raise LeakCheckError("Invalid phone number format", 400)

        return True

    def _get_hash(self, value: str, truncate: bool = True) -> str:
        """Generate SHA256 hash of a value"""
        hash_obj = hashlib.sha256(value.lower().encode())
        hash_value = hash_obj.hexdigest()
        return hash_value[:24] if truncate else hash_value

    async def search(self, query: str, search_type: SearchType = SearchType.AUTO, 
                    limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Search LeakCheck API with various query types
        
        Args:
            query: Search query
            search_type: Type of search (default: auto)
            limit: Maximum results (max 1000)
            offset: Result offset (max 2500)
        """
        try:
            # Validate parameters
            self._validate_query(query, search_type)
            if limit > 1000:
                limit = 1000
            if offset > 2500:
                offset = 2500

            # Check rate limit
            if not await self.check_rate_limit('leakcheck'):
                raise LeakCheckError("Daily rate limit exceeded", 429)

            # Check cache
            cache_key = f"leakcheck:{search_type.value}:{query}:{limit}:{offset}"
            cached_result = self.rate_limiter.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # Prepare API call
            api = LeakCheckAPI_v2(api_key=self.leakcheck_key)
            params = {
                'query': query,
                'type': search_type.value,
                'limit': limit,
                'offset': offset
            }

            # Make API call
            result = await asyncio.to_thread(
                api.lookup,
                **params
            )

            # Process and format results
            formatted_result = self._format_results(result)

            # Cache results
            self.rate_limiter.setex(
                cache_key,
                86400,  # 24 hours
                json.dumps(formatted_result)
            )

            return formatted_result

        except LeakCheckError as e:
            self.logger.error(f"LeakCheck API error: {e.message} (Status: {e.status_code})")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in LeakCheck search: {str(e)}")
            raise

    def _format_results(self, raw_results: List[Dict]) -> Dict[str, Any]:
        """Format raw API results into structured data"""
        formatted_results = []
        sources = set()
        passwords_found = False

        for entry in raw_results:
            source = entry.get('source', {})
            sources.add(source.get('name', ''))
            
            if entry.get('password'):
                passwords_found = True

            formatted_results.append({
                "API": "LeakCheck",
                "Password": entry.get('password', 'N/A'),
                "Source_Name": source.get('name'),
                "Breach_Date": source.get('breach_date'),
                "Unverified": source.get('unverified', False),
                "Passwordless": source.get('passwordless', True),
                "Compilation": source.get('compilation', False),
                "Email": entry.get('email', 'N/A'),
                "Username": entry.get('username', 'N/A'),
                "Name": entry.get('name', 'N/A'),
                "Country": entry.get('country', 'N/A'),
                "Fields": entry.get('fields', [])
            })

        return {
            "results": formatted_results,
            "summary": {
                "total_sources": len(sources),
                "sources_list": list(sources),
                "total_results": len(formatted_results),
                "contains_passwords": passwords_found
            }
        }

    async def check_email_leaks(self, email: str) -> Dict[str, Any]:
        """Enhanced email leak check with multiple search methods"""
        try:
            results = await asyncio.gather(
                self.search(email, SearchType.EMAIL),
                self.search(self._get_hash(email), SearchType.HASH),
                return_exceptions=True
            )

            combined_results = {
                'email': email,
                'total_leaks': 0,
                'results': [],
                'sources': set(),
                'has_password_leak': False
            }

            for result in results:
                if isinstance(result, Dict):
                    combined_results['results'].extend(result.get('results', []))
                    combined_results['sources'].update(
                        result.get('summary', {}).get('sources_list', [])
                    )
                    if result.get('summary', {}).get('contains_passwords'):
                        combined_results['has_password_leak'] = True

            combined_results['total_leaks'] = len(combined_results['results'])
            combined_results['sources'] = list(combined_results['sources'])

            return combined_results

        except Exception as e:
            self.logger.error(f"Error in enhanced email leak check: {str(e)}")
            raise

    async def get_usage_stats(self) -> Dict[str, int]:
        """Get current API usage statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        stats = {}
        
        for api_name in ['dehashed', 'leakcheck']:
            key = f"leak_check:{api_name}:{today}"
            usage = int(self.rate_limiter.get(key) or 0)
            limit = Config.DAILY_LIMITS['leak_check'][api_name]
            stats[api_name] = {
                'usage': usage,
                'limit': limit,
                'remaining': max(0, limit - usage)
            }
            
        return stats

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
        self.rate_limiter.close() 

    async def check_dehashed(self, entry: str, search_type: DehashedSearchType = DehashedSearchType.EMAIL, page: int = 1) -> List[Dict[str, Any]]:
        """Check entry against Dehashed API with specific search type"""
        url = "https://api.checkleaked.cc/api/dehashed"
        headers = {
            "accept": "application/json",
            "api-key": self.dehashed_key,
            "Content-Type": "application/json"
        }
        payload = {
            "entry": entry,
            "type": search_type.value,
            "page": page
        }

        try:
            session = await self.get_session()
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    if "entries" in data:
                        for entry in data["entries"]:
                            if "entry" in entry:
                                entry_data = entry["entry"]
                                result = {
                                    "API": "Dehashed",
                                    "ID": entry_data.get("id"),
                                    "Email": entry_data.get("email"),
                                    "Username": entry_data.get("username"),
                                    "Password": entry_data.get("password"),
                                    "Hashed_Password": entry_data.get("hashed_password"),
                                    "Name": entry_data.get("name"),
                                    "VIN": entry_data.get("vin"),
                                    "Address": entry_data.get("address"),
                                    "IP_Address": entry_data.get("ip_address"),
                                    "Phone": entry_data.get("phone"),
                                    "Obtained_From": entry_data.get("obtained_from"),
                                    "Hash_Type": entry_data.get("hash_type"),
                                    "Search_Type": search_type.value
                                }
                                results.append(result)
                    return results
                else:
                    self.logger.error(f"Dehashed API error: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Error checking Dehashed: {str(e)}")
            return []

    async def check_experimental(self, entry: str, search_type: ExperimentalSearchType = ExperimentalSearchType.EMAIL) -> List[Dict[str, Any]]:
        """Check entry against Experimental API with specific search type"""
        try:
            api = LeakCheckAPI_v2(api_key=self.leakcheck_key)
            params = {
                'query': entry,
                'type': search_type.value,
                'limit': 100
            }
            
            result = await asyncio.to_thread(api.lookup, **params)

            results = []
            for entry in result:
                results.append({
                    "API": "LeakCheck",
                    "Password": entry.get('password', 'N/A'),
                    "Source_Name": entry['source']['name'],
                    "Breach_Date": entry['source']['breach_date'],
                    "Unverified": entry['source']['unverified'],
                    "Passwordless": entry['source']['passwordless'],
                    "Compilation": entry['source']['compilation'],
                    "Email": entry.get('email', 'N/A'),
                    "Username": entry.get('username', 'N/A'),
                    "Name": entry.get('name', 'N/A'),
                    "Country": entry.get('country', 'N/A'),
                    "Fields": entry.get('fields', []),
                    "Search_Type": search_type.value
                })
            return results
        except Exception as e:
            self.logger.error(f"Error checking Experimental: {str(e)}")
            return []

    async def comprehensive_check(self, entry: str) -> Dict[str, Any]:
        """Perform comprehensive check using both APIs and multiple search types"""
        try:
            tasks = [
                # Dehashed checks
                self.check_dehashed(entry, DehashedSearchType.EMAIL),
                self.check_dehashed(entry, DehashedSearchType.USERNAME),
                
                # Experimental checks
                self.check_experimental(entry, ExperimentalSearchType.EMAIL),
                self.check_experimental(entry, ExperimentalSearchType.USERNAME),
                self.check_experimental(entry, ExperimentalSearchType.HASH)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            combined_results = {
                'entry': entry,
                'total_findings': 0,
                'dehashed_results': [],
                'experimental_results': [],
                'has_password_leak': False,
                'unique_sources': set(),
                'timestamp': datetime.now().isoformat()
            }

            for result in results:
                if isinstance(result, list):
                    for item in result:
                        if item['API'] == 'Dehashed':
                            combined_results['dehashed_results'].append(item)
                        else:
                            combined_results['experimental_results'].append(item)
                        
                        if item.get('Password') not in ['N/A', None, '']:
                            combined_results['has_password_leak'] = True
                        
                        if item.get('Source_Name'):
                            combined_results['unique_sources'].add(item['Source_Name'])

            combined_results['total_findings'] = (
                len(combined_results['dehashed_results']) + 
                len(combined_results['experimental_results'])
            )
            combined_results['unique_sources'] = list(combined_results['unique_sources'])

            return combined_results

        except Exception as e:
            self.logger.error(f"Error in comprehensive check: {str(e)}")
            raise 