import asyncio
import uvicorn
from fastapi import FastAPI
from api.business_api import BusinessAPI
from message_queue.message_queue import QueueConsumer
from utils.logger import Logger
from typing import Dict, Any

app = FastAPI()
business_api = BusinessAPI()
consumer = QueueConsumer()
logger = Logger("main")

async def handle_message(message: Dict[str, Any]):
    """Handle incoming messages from RabbitMQ"""
    try:
        logger.info(f"Received message: {message}")
        
        # Handle different message types
        message_type = message.get('type')
        if message_type == 'search':
            # Handle search request
            result = await business_api.search_businesses(message.get('data', {}))
            logger.info(f"Search result: {result}")
        elif message_type == 'create':
            # Handle create business request
            result = await business_api.create_business(message.get('data', {}))
            logger.info(f"Create result: {result}")
        elif message_type == 'update':
            # Handle update business request
            business_id = message.get('business_id')
            result = await business_api.update_business(business_id, message.get('data', {}))
            logger.info(f"Update result: {result}")
        elif message_type == 'delete':
            # Handle delete business request
            business_id = message.get('business_id')
            result = await business_api.delete_business(business_id)
            logger.info(f"Delete result: {result}")
        else:
            logger.warning(f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Start the application and message consumer"""
    try:
        logger.info("Starting up the application")
        # Start the queue consumer with message handler
        asyncio.create_task(consumer.start(handle_message))
        logger.info("Message consumer started")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    try:
        logger.info("Shutting down the application")
        await consumer.close()
        await business_api.close()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)