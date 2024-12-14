import asyncio
import aio_pika
import json
from typing import Dict, Any, Callable
from utils.logger import Logger
from config import Config

class QueueConsumer:
    def __init__(self):
        self.logger = Logger("queue_consumer")
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                login=Config.RABBITMQ_USER,
                password=Config.RABBITMQ_PASS
            )
            self.channel = await self.connection.channel()
            self.logger.info("Connected to RabbitMQ")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def setup_queue(self):
        """Setup exchange and queue"""
        try:
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                "business_exchange",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                "business_queue",
                durable=True
            )
            
            # Bind queue to exchange
            await self.queue.bind(
                self.exchange,
                routing_key="business"
            )
            
            self.logger.info("Queue setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup queue: {str(e)}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process incoming message"""
        try:
            async with message.process():
                data = json.loads(message.body.decode())
                self.logger.info(f"Processing message: {data}")
                # Process the message here
                # You can add your business logic
                
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            # Reject the message
            await message.reject()

    async def start(self):
        """Start consuming messages"""
        try:
            if not self.connection:
                await self.connect()
                await self.setup_queue()
            
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.process_message(message)
                    
        except Exception as e:
            self.logger.error(f"Error in consumer: {str(e)}")
            if self.connection:
                await self.connection.close()
            raise

    async def close(self):
        """Close the connection"""
        if self.connection:
            await self.connection.close()
