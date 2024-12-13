import asyncio
from workers.leak_check_worker import LeakCheckWorker
from utils.logger import Logger

async def main():
    logger = Logger('main')
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

if __name__ == "__main__":
    asyncio.run(main())