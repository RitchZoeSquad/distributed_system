import asyncio
from message_queue.message_queue import QueueConsumer
from utils.logger import Logger

logger = Logger('main')
consumer = QueueConsumer()

async def message_handler(data):
    try:
        operation = data.get('operation')
        if operation == 'business':
            await consumer.process_business(data)
        else:
            logger.warning(f"Unknown operation: {operation}")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        raise

async def main():
    try:
        logger.info("Starting business worker...")
        await consumer.start_consuming(message_handler)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await consumer.close()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
