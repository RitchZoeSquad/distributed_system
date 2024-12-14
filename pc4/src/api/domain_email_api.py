import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any, Optional
from datetime import datetime
import json
import aio_pika
from api.shodan_api import ShodanAPI

class DomainEmailAPI:
    def __init__(self):
        self.tomba_key = "ta_5xbwm66o5844vy6mqdpecnplz83wyhcq6uwaz"
        self.tomba_secret = "ts_27bd86ee-7947-46f5-b695-5f32a217be2e"
        self.logger = Logger('domain_email_api')
        self.session = None
        self.base_url = "https://api.tomba.io/v1"
        self.connection = None
        self.channel = None
        self.queue_name = "domain_email_queue"

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

    async def connect_rabbitmq(self):
        """Connect to RabbitMQ"""
        try:
            # Create connection
            self.connection = await aio_pika.connect_robust(
                host=Config.RABBITMQ_CONFIG['host'],
                port=Config.RABBITMQ_CONFIG['port'],
                login=Config.RABBITMQ_CONFIG['user'],
                password=Config.RABBITMQ_CONFIG['password'],
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue
            queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            self.logger.info("Connected to RabbitMQ")
            return queue
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

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
            leak_check_api = LeakCheckAPI()
            
            if domain_data and 'data' in domain_data and 'emails' in domain_data['data']:
                for email_entry in domain_data['data']['emails'][:5]:  # Limit to first 5 emails
                    email = email_entry.get('email')
                    if email:
                        # Get email enrichment data
                        enriched_data = await self.enrich_email(email)
                        
                        # Check for email leaks
                        leak_data = await leak_check_api.comprehensive_check(email)
                        
                        if enriched_data:
                            email_info = self._extract_email_info(enriched_data)
                            email_info['leak_data'] = leak_data
                            emails_info.append(email_info)

            await leak_check_api.close()

            # Get comprehensive Shodan data for the domain
            shodan_api = ShodanAPI()
            shodan_data = await shodan_api.get_domain_info(domain)
            await shodan_api.close()

            if shodan_data:
                org_info['shodan_data'] = {
                    'ssl_certificates': shodan_data.get('ssl_certificates', []),
                    'open_ports': shodan_data.get('open_ports', []),
                    'technologies': shodan_data.get('technologies', []),
                    'cloud_assets': shodan_data.get('cloud_assets', []),
                    'screenshots': shodan_data.get('screenshots', []),
                    'security_issues': {
                        'vulnerable_services': [],
                        'exposed_ports': [],
                        'ssl_issues': []
                    }
                }

                # Analyze security issues
                for port in org_info['shodan_data']['open_ports']:
                    if port in [3389, 22, 3306, 1433]:  # Common sensitive ports
                        org_info['shodan_data']['security_issues']['exposed_ports'].append({
                            'port': port,
                            'risk': 'high',
                            'description': f'Potentially sensitive port {port} exposed'
                        })

                # Check SSL certificates
                for cert in org_info['shodan_data']['ssl_certificates']:
                    if cert.get('expires'):
                        # Add SSL expiration warning if within 30 days
                        try:
                            expires = datetime.fromisoformat(cert['expires'].replace('Z', '+00:00'))
                            if (expires - datetime.now(expires.tzinfo)).days < 30:
                                org_info['shodan_data']['security_issues']['ssl_issues'].append({
                                    'type': 'expiration',
                                    'description': f'SSL Certificate expiring soon: {cert["expires"]}'
                                })
                        except Exception as e:
                            self.logger.error(f"Error parsing SSL expiration: {str(e)}")

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
        """Close all connections"""
        if self.session and not self.session.closed:
            await self.session.close()
        
        if self.connection:
            await self.connection.close()
            self.logger.info("Closed RabbitMQ connection")

    async def schedule_leak_check(self, email: str):
        """Schedule an email for leak checking"""
        try:
            await self.connect_rabbitmq()
            
            message = {
                'email': email,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    content_type='application/json'
                ),
                routing_key=Config.RABBITMQ_CONFIG['queues']['leak_check']
            )
            
            self.logger.info(f"Scheduled leak check for email: {email}")
            
        except Exception as e:
            self.logger.error(f"Error scheduling leak check: {str(e)}")
            raise