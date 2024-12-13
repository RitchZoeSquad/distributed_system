import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any, Optional
from datetime import datetime

class DomainEmailAPI:
    def __init__(self):
        self.tomba_key = "ta_5xbwm66o5844vy6mqdpecnplz83wyhcq6uwaz"
        self.tomba_secret = "ts_27bd86ee-7947-46f5-b695-5f32a217be2e"
        self.logger = Logger('domain_email_api')
        self.session = None
        self.base_url = "https://api.tomba.io/v1"

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json",
                    "X-Tomba-Key": self.tomba_key,
                    "X-Tomba-Secret": self.tomba_secret,
                    "User-Agent": f"DomainEmailWorker-{Config.PC_ID}"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    def _extract_organization_info(self, domain_data: Dict) -> Dict[str, Any]:
        """Extract relevant organization information from domain search response"""
        org = domain_data.get('data', {}).get('organization', {})
        return {
            'company_name': org.get('organization'),
            'company_size': org.get('company_size'),
            'industry': org.get('industries'),
            'founded': org.get('founded'),
            'location': {
                'country': org.get('location', {}).get('country'),
                'city': org.get('location', {}).get('city'),
                'state': org.get('location', {}).get('state'),
                'postal_code': org.get('location', {}).get('postal_code')
            },
            'social_links': org.get('social_links', {}),
            'description': org.get('description'),
            'website': org.get('website_url'),
            'pattern': org.get('pattern'),
            'last_updated': org.get('last_updated')
        }

    def _extract_email_info(self, email_data: Dict) -> Dict[str, Any]:
        """Extract relevant email information from enrichment response"""
        data = email_data.get('data', {})
        return {
            'email': data.get('email'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'full_name': data.get('full_name'),
            'position': data.get('position'),
            'company': data.get('company'),
            'linkedin': data.get('linkedin'),
            'score': data.get('score'),
            'verification': data.get('verification', {}),
            'country': data.get('country'),
            'gender': data.get('gender'),
            'sources': [
                {
                    'url': source.get('uri'),
                    'website': source.get('website_url'),
                    'last_seen': source.get('last_seen_on')
                }
                for source in data.get('sources', [])[:3]  # Limit to first 3 sources
            ]
        }

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def search_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Search for email data associated with a domain"""
        try:
            session = await self.get_session()
            self.logger.info(f"Searching domain: {domain}")
            
            async with session.get(
                f"{self.base_url}/domain-search",
                params={"domain": domain, "limit": 10}  # Limit to 10 emails per domain
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Domain search successful for: {domain}")
                    return result
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Domain API rate limit exceeded, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    self.logger.error(f"Domain API Error: {response.status} - {error_text}")
                    return None

        except Exception as e:
            self.logger.error(f"Domain search failed for {domain}: {str(e)}")
            return None

    async def enrich_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Enrich email data with additional information"""
        try:
            session = await self.get_session()
            self.logger.info(f"Enriching email: {email}")
            
            async with session.get(
                f"{self.base_url}/enrich",
                params={"email": email}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Email enrichment successful for: {email}")
                    return result
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Email API rate limit exceeded, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    self.logger.error(f"Email API Error: {response.status} - {error_text}")
                    return None

        except Exception as e:
            self.logger.error(f"Email enrichment failed for {email}: {str(e)}")
            return None

    async def validate_domain_and_email(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate both domain and email for a business"""
        try:
            # Extract domain from business data
            website = business_data.get('website', '')
            if not website:
                self.logger.warning("No website provided for domain/email validation")
                return None

            # Clean domain (remove http/https and www if present)
            domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

            # Get domain data
            domain_data = await self.search_domain(domain)
            if not domain_data:
                return None

            # Process organization info
            org_info = self._extract_organization_info(domain_data)
            
            # Process email data
            emails_info = []
            if domain_data and 'data' in domain_data and 'emails' in domain_data['data']:
                for email_entry in domain_data['data']['emails'][:5]:  # Limit to first 5 emails
                    email = email_entry.get('email')
                    if email:
                        enriched_data = await self.enrich_email(email)
                        if enriched_data:
                            emails_info.append(self._extract_email_info(enriched_data))

            return {
                'business_id': business_data.get('business_id'),
                'domain': domain,
                'organization': org_info,
                'emails': emails_info,
                'processed_date': datetime.now().isoformat(),
                'processed_by': Config.PC_ID
            }

        except Exception as e:
            self.logger.error(f"Domain/Email validation failed: {str(e)}")
            return None

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None