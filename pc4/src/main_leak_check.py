import asyncio
from message_queue.message_queue import QueueConsumer
from utils.logger import Logger
from utils.metrics import start_metrics_server

logger = Logger('main')
consumer = QueueConsumer()

async def message_handler(data):
    try:
        operation = data.get('operation')
        if operation == 'leak_check':
            await consumer.process_leak_check(data.get('email'))
        else:
            logger.warning(f"Unknown operation: {operation}")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        raise

async def main():
    try:
        # Start metrics server
        start_metrics_server()
        
        logger.info("Starting leak check worker...")
        await consumer.start_consuming(message_handler)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await consumer.close()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())