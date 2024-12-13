import asyncio
import uvicorn
from fastapi import FastAPI
from config import Config
from api.business_api import BusinessAPI
from database.db_manager import DatabaseManager
from queue.consumer import QueueConsumer
from redis.rate_limiter import RateLimiter
from utils.logger import Logger
from utils.metrics import MetricsCollector

# Create FastAPI app for health checks
app = FastAPI()

class BusinessWorker:
    def __init__(self):
        self.logger = Logger(Config.PC_ID)
        self.db = DatabaseManager()
        self.api = BusinessAPI()
        self.consumer = QueueConsumer()
        self.rate_limiter = RateLimiter()
        self.metrics = MetricsCollector()

    async def process_business(self, data):
        try:
            if await self.rate_limiter.can_make_request():
                self.logger.info(f"Processing business: {data['business_id']}")
                
                # Start timing the processing
                start_time = self.metrics.time()
                
                # Make API request
                result = await self.api.search_business(data)
                
                # Store results
                await self.db.insert_business(result)
                
                # Update metrics
                self.metrics.increment_processed_businesses()
                self.metrics.observe_processing_time(start_time)
                
                # Update rate limiter
                await self.rate_limiter.increment_usage()
                
                return result
            else:
                self.logger.warning("Rate limit exceeded")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing business: {str(e)}")
            self.metrics.increment_api_errors()
            raise

    async def start(self):
        self.logger.info(f"Starting Business Worker on {Config.PC_ID}")
        await self.consumer.start_consuming(self.process_business)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "pc_id": Config.PC_ID}

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
    worker = BusinessWorker()
    await asyncio.gather(
        worker.start(),
        start_server()
    )

if __name__ == "__main__":
    asyncio.run(main())