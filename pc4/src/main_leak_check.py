import asyncio
from workers.leak_check_worker import LeakCheckWorker
from utils.logger import Logger
from fastapi import FastAPI
from api.health import router as health_router

app = FastAPI()
app.include_router(health_router)

async def start_worker():
    logger = Logger('main_leak_check')
    worker = LeakCheckWorker()
    
    try:
        logger.info("Starting leak check worker")
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down leak check worker")
        await worker.stop()
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        await worker.stop()
        raise

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_worker())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 