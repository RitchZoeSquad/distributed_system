import aiohttp
import asyncio
from config import Config
from utils.logger import Logger
import backoff
from typing import Dict, Any

class PhoneAPI:
    def __init__(self):
        self.api_key = Config.API_KEYS['phone']
        self.logger = Logger('phone_api')
        self.session = None
        self.retry_config = Config.RETRY_CONFIG

    async def get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": f"PhoneValidator-{Config.PC_ID}"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def validate_phone(self, phone: str) -> Dict[str, Any]:
        try:
            session = await self.get_session()
            self.logger.info(f"Validating phone: {phone}")
            
            async with session.post(
                f"{Config.API_ENDPOINTS['phone']}/validate",
                json={"phone": phone}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Phone validation successful: {phone}")
                    return {
                        'phone': phone,
                        'status': result.get('status', 'unknown'),
                        'type': result.get('type', 'unknown'),
                        'carrier': result.get('carrier', 'unknown'),
                        'country': result.get('country', 'unknown'),
                        'valid': result.get('valid', False),
                        'formatting': {
                            'international': result.get('international_format'),
                            'local': result.get('local_format')
                        }
                    }
                elif response.status == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Phone API rate limit exceeded, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    self.logger.error(f"Phone API Error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(f"Phone API Error: {response.status}")

        except asyncio.TimeoutError:
            self.logger.error(f"Phone validation timeout for: {phone}")
            raise
        except Exception as e:
            self.logger.error(f"Phone validation failed for {phone}: {str(e)}")
            raise

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3
    )
    async def validate_phone_batch(self, phones: list) -> Dict[str, Any]:
        try:
            session = await self.get_session()
            self.logger.info(f"Validating phone batch of {len(phones)} numbers")
            
            async with session.post(
                f"{Config.API_ENDPOINTS['phone']}/validate/batch",
                json={"phones": phones}
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    self.logger.info(f"Batch phone validation successful for {len(phones)} numbers")
                    return results
                elif response.status == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Phone API rate limit exceeded, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    error_text = await response.text()
                    self.logger.error(f"Phone API Error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(f"Phone API Error: {response.status}")

        except Exception as e:
            self.logger.error(f"Batch phone validation failed: {str(e)}")
            raise

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None