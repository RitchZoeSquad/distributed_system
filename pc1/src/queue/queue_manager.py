import aio_pika
from typing import Dict, Any
import json
from utils.logger import Logger

class QueueManager:
    def __init__(self):
        self.logger = Logger('queue_manager')
        self.connection = None
        self.channel = None
        
        # Exchange and queue names
        self.exchange_name = 'shodan_exchange'
        self.search_queue = 'shodan_search_queue'
        self.host_queue = 'shodan_host_queue'
        self.search_routing_key = 'search'
        self.host_routing_key = 'host'

    async def connect(self):
        """Connect to RabbitMQ and set up exchanges/queues"""
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(
                host="rabbitmq",
                port=5672,
                login="zoeman",
                password="TestingPurposes9!"
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
            
            # Declare queues
            search_queue = await self.channel.declare_queue(
                self.search_queue,
                durable=True
            )
            host_queue = await self.channel.declare_queue(
                self.host_queue,
                durable=True
            )
            
            # Bind queues to exchange
            await search_queue.bind(
                exchange,
                routing_key=self.search_routing_key
            )
            await host_queue.bind(
                exchange,
                routing_key=self.host_routing_key
            )
            
            self.logger.info("Successfully connected to RabbitMQ and set up queues")
            
        except Exception as e:
            self.logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            raise

    async def publish_search_task(self, query: str):
        """Publish a search task to RabbitMQ"""
        try:
            message = {
                'query': query,
                'type': 'search'
            }
            
            await self._publish_message(
                message,
                self.search_routing_key
            )
            
        except Exception as e:
            self.logger.error(f"Error publishing search task: {str(e)}")
            raise

    async def publish_host_task(self, ip: str):
        """Publish a host information task to RabbitMQ"""
        try:
            message = {
                'ip': ip,
                'type': 'host'
            }
            
            await self._publish_message(
                message,
                self.host_routing_key
            )
            
        except Exception as e:
            self.logger.error(f"Error publishing host task: {str(e)}")
            raise

    async def _publish_message(self, message: Dict[str, Any], routing_key: str):
        """Helper method to publish messages"""
        if not self.channel:
            await self.connect()
            
        exchange = await self.channel.get_exchange(self.exchange_name)
        
        message_body = json.dumps(message).encode()
        await exchange.publish(
            aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )
        
        self.logger.info(f"Published message with routing key {routing_key}")

    async def close(self):
        """Close the RabbitMQ connection"""
        if self.connection:
            await self.connection.close()
