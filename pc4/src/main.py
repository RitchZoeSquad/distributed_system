import asyncio
import uvicorn
from fastapi import FastAPI
from config import Config
from api.domain_email_api import DomainEmailAPI
from api.phone_api import PhoneAPI
from database.db_manager import DatabaseManager
from queue.consumer import QueueConsumer
from redis.rate_limiter import RateLimiter
from utils.logger import Logger
from utils.metrics import MetricsCollector

# Create FastAPI app for health checks
app = FastAPI()

class ValidationWorker:
    def __init__(self):
        self.logger = Logger(Config.PC_ID)
        self.db = DatabaseManager()
        self.domain_email_api = DomainEmailAPI()
        self.phone_api = PhoneAPI()
        self.consumer = QueueConsumer()
        self.rate_limiter = RateLimiter()
        self.metrics = MetricsCollector()

    async def process_domain_email(self, data):
        try:
            if await self.rate_limiter.can_make_request('domain_email'):
                self.logger.info(f"Processing domain/email for business: {data['business_id']}")
                start_time = self.metrics.time()

                # Validate domain and email
                domain_result = await self.domain_email_api.validate_domain(data['domain'])
                email_result = await self.domain_email_api.validate_email(data['email'])

                # Store results
                await self.db.insert_domain_email_validation({
                    'business_id': data['business_id'],
                    'domain': data['domain'],
                    'domain_status': domain_result['status'],
                    'email': data['email'],
                    'email_status': email_result['status'],
                    'validation_details': {
                        'domain': domain_result,
                        'email': email_result
                    }
                })

                # Update metrics
                self.metrics.observe_processing_time('domain_email', start_time)
                self.metrics.increment_processed_validations('domain_email')
                await self.rate_limiter.increment_usage('domain_email')

                return {'domain': domain_result, 'email': email_result}
            else:
                self.logger.warning("Domain/Email rate limit exceeded")
                return None

        except Exception as e:
            self.logger.error(f"Error processing domain/email: {str(e)}")
            self.metrics.increment_validation_errors('domain_email')
            raise

    async def process_phone(self, data):
        try:
            if await self.rate_limiter.can_make_request('phone'):
                self.logger.info(f"Processing phone for business: {data['business_id']}")
                start_time = self.metrics.time()

                # Validate phone
                phone_result = await self.phone_api.validate_phone(data['phone'])

                # Store results
                await self.db.insert_phone_validation({
                    'business_id': data['business_id'],
                    'phone': data['phone'],
                    'validation_status': phone_result['status'],
                    'validation_details': phone_result
                })

                # Update metrics
                self.metrics.observe_processing_time('phone', start_time)
                self.metrics.increment_processed_validations('phone')
                await self.rate_limiter.increment_usage('phone')

                return phone_result
            else:
                self.logger.warning("Phone rate limit exceeded")
                return None

        except Exception as e:
            self.logger.error(f"Error processing phone: {str(e)}")
            self.metrics.increment_validation_errors('phone')
            raise

    async def start(self):
        self.logger.info(f"Starting Validation Worker on {Config.PC_ID}")
        try:
            await asyncio.gather(
                self.consumer.start_consuming('domain_email', self.process_domain_email),
                self.consumer.start_consuming('phone', self.process_phone),
                self.metrics.collect_metrics()
            )
        except Exception as e:
            self.logger.error(f"Critical error in worker: {str(e)}")
            raise

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "pc_id": Config.PC_ID,
        "service_type": "domain_email_phone_validator"
    }

@app.get("/metrics")
async def get_metrics():
    return {
        "domain_email_daily_usage": await RateLimiter().get_current_usage('domain_email'),
        "phone_daily_usage": await RateLimiter().get_current_usage('phone')
    }

async def start_server():
    config = uvicorn.Config(
        app, 
        host="0.0.0.0", 
        port=Config.HEALTH_CHECK_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    worker = ValidationWorker()
    await asyncio.gather(
        worker.start(),
        start_server()
    )

if __name__ == "__main__":
    asyncio.run(main())