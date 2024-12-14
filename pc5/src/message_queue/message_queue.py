import json
import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from config import Config
from utils.logger import Logger
from typing import Callable, Any
import backoff
from datetime import datetime

class QueueConsumer:
    def __init__(self):
        self.config = Config.RABBITMQ_CONFIG
        self.logger = Logger('queue_consumer')
        self.connection = None
        self.channel = None
        self.processing = False
        self._connection_lock = asyncio.Lock()

    async def connect(self):
        async with self._connection_lock:
            if not self.connection or self.connection.is_closed:
                self.logger.info(f"Connecting to RabbitMQ at {self.config['url']}")
                try:
                    self.connection = await aio_pika.connect_robust(
                        self.config['url'],
                        client_properties={
                            'connection_name': f'pc5_business_worker'
                        }
                    )
                    self.channel = await self.connection.channel()
                    await self.channel.set_qos(prefetch_count=1)
                    
                    # Declare exchange
                    exchange = await self.channel.declare_exchange(
                        self.config['exchange_name'],
                        aio_pika.ExchangeType.TOPIC,
                        durable=True
                    )
                    
                    # Declare queue
                    queue = await self.channel.declare_queue(
                        self.config['queue_name'],
                        durable=True
                    )
                    
                    # Bind queue to exchange
                    await queue.bind(
                        exchange=exchange,
                        routing_key=self.config['routing_key']
                    )
                    
                    self.logger.info("Successfully connected to RabbitMQ")
                    return queue
                except Exception as e:
                    self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
                    raise

    async def process_message(self, message: AbstractIncomingMessage, callback: Callable):
        async with message.process():
            try:
                body = message.body.decode()
                data = json.loads(body)
                self.logger.info(f"Processing message: {data}")
                await callback(data)
                self.logger.info("Message processed successfully")
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                raise

    async def start_consuming(self, callback: Callable):
        while True:
            try:
                queue = await self.connect()
                self.logger.info("Starting to consume messages...")
                
                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        await self.process_message(message, callback)
                        
            except Exception as e:
                self.logger.error(f"Error in consumer: {str(e)}")
                if self.connection and not self.connection.is_closed:
                    await self.connection.close()
                await asyncio.sleep(5)  # Wait before reconnecting

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.logger.info("RabbitMQ connection closed")
