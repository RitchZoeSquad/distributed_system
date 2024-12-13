import asyncio
import uvicorn
from fastapi import FastAPI
from config import Config
from api.serp_api import SerpAPI
from database.db_manager import DatabaseManager
from queue.consumer import QueueConsumer
from redis.rate_limiter import RateLimiter
from utils.logger import Logger
from utils.metrics import MetricsCollector

# Create FastAPI app for health checks
app = FastAPI()

class SerpWorker:
    def __init__(self):
        self.logger = Logger(Config.PC_ID)
        self.db = DatabaseManager()
        self.api = SerpAPI()
        self.consumer = QueueConsumer()
        self.rate_limiter = RateLimiter()
        self.metrics = MetricsCollector()

    async def process_serp_query(self, data):
        try:
            if await self.rate_limiter.can_make_request():
                self.logger.info(f"Processing SERP query for business: {data['business_id']}")
                start_time = self.metrics.time()

                # Construct search query
                query = f"{data.get('name', '')} {data.get('address', '')}"
                
                # Make SERP API request
                serp_result = await self.api.search(query, data.get('parameters', {}))
                
                # Store results
                await self.db.insert_serp_result({
                    'business_id': data['business_id'],
                    'query': query,
                    'results': serp_result
                })

                # Update metrics
                self.metrics.observe_processing_time(start_time)
                self.metrics.increment_processed_queries()
                await self.rate_limiter.increment_usage()

                return serp_result
            else:
                self.logger.warning("SERP rate limit exceeded")
                return None

        except Exception as e:
            self.logger.error(f"Error processing SERP query: {str(e)}")
            self.metrics.increment_api_errors()
            raise

    async def start(self):
        self.logger.info(f"Starting SERP Worker on {Config.PC_ID}")
        try:
            await asyncio.gather(
                self.consumer.start_consuming(self.process_serp_query),
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
        "service_type": "serp_worker"
    }

@app.get("/metrics")
async def get_metrics():
    rate_limiter = RateLimiter()
    return {
        "daily_usage": await rate_limiter.get_current_usage(),
        "remaining_quota": Config.DAILY_LIMIT - await rate_limiter.get_current_usage()
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
    worker = SerpWorker()
    await asyncio.gather(
        worker.start(),
        start_server()
    )

if __name__ == "__main__":
    asyncio.run(main())