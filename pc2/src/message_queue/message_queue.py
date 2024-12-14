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
            config = Config.RABBITMQ_CONFIG
            self.logger.info(f"Connecting to RabbitMQ at {config['host']}:{config['port']}")
            
            # Build connection URL
            url = f"amqp://{config['user']}:{config['password']}@{config['host']}:{config['port']}/"
            self.logger.info(f"Connection URL (without credentials): amqp://***:***@{config['host']}:{config['port']}/")
            
            self.connection = await aio_pika.connect_robust(url)
            self.channel = await self.connection.channel()
            self.logger.info("Connected to RabbitMQ")
            
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                config['exchange_name'],
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                config['queue_name'],
                durable=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def close(self):
        """Close the connection"""
        if self.connection:
            await self.connection.close()
            self.logger.info("Closed RabbitMQ connection")

    async def start(self, callback: Callable[[Dict[str, Any]], None]):
        """Start consuming messages"""
        try:
            await self.connect()
            
            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        body = message.body.decode()
                        data = json.loads(body)
                        self.logger.info(f"Received message: {data}")
                        await callback(data)
                    except Exception as e:
                        self.logger.error(f"Error processing message: {str(e)}")
            
            await self.queue.consume(process_message)
            self.logger.info("Started consuming messages")
            
            try:
                await asyncio.Future()  # run forever
            except Exception as e:
                self.logger.error(f"Consumer interrupted: {str(e)}")
                await self.close()
                
        except Exception as e:
            self.logger.error(f"Failed to start consumer: {str(e)}")
            await self.close()
            raise
