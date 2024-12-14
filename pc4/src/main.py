import asyncio
from message_queue.message_queue import QueueConsumer
from utils.logger import Logger
from api.business_api import BusinessAPI

logger = Logger('main')
consumer = QueueConsumer()
business_api = BusinessAPI()

async def message_handler(data):
    try:
        operation = data.get('operation')
        if operation == 'search':
            await business_api.search_businesses(data.get('query', {}))
        elif operation == 'create':
            await business_api.create_business(data.get('business_data', {}))
        elif operation == 'update':
            await business_api.update_business(data.get('business_id'), data.get('business_data', {}))
        elif operation == 'delete':
            await business_api.delete_business(data.get('business_id'))
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
        await business_api.close()
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())