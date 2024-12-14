import asyncio
import json
import aio_pika
from config import Config
from utils.logger import Logger
from api.leak_check_api import LeakCheckAPI
from api.domain_email_api import DomainEmailAPI

class QueueConsumer:
    def __init__(self):
        self.logger = Logger('queue_consumer')
        self.connection = None
        self.channel = None
        self.queue_name = None
        self.leak_check_api = LeakCheckAPI()
        self.domain_email_api = DomainEmailAPI()

        # Set queue name based on service type
        service_type = Config.SERVICE_TYPE
        if service_type == 'leak_check':
            self.queue_name = Config.RABBITMQ_CONFIG['queues']['leak_check']
        elif service_type == 'domain_email':
            self.queue_name = Config.RABBITMQ_CONFIG['queues']['domain_email']
        else:
            raise ValueError(f"Invalid service type: {service_type}")

    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            # Build connection URL
            rabbitmq_url = f"amqp://{Config.RABBITMQ_CONFIG['user']}:{Config.RABBITMQ_CONFIG['password']}@{Config.RABBITMQ_CONFIG['host']}:{Config.RABBITMQ_CONFIG['port']}/"
            self.logger.info(f"Connecting to RabbitMQ at {rabbitmq_url}")

            # Create connection
            self.connection = await aio_pika.connect_robust(
                rabbitmq_url,
                client_properties={
                    "connection_name": f"pc4_{Config.SERVICE_TYPE}_worker"
                }
            )

            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)

            # Declare queue
            queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )

            self.logger.info("Successfully connected to RabbitMQ")
            return queue

        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def process_leak_check(self, email):
        """Process a leak check request"""
        try:
            result = await self.leak_check_api.check_leaks(email)
            self.logger.info(f"Successfully processed leak check for {email}")
            return result
        except Exception as e:
            self.logger.error(f"Error processing leak check for {email}: {str(e)}")
            raise

    async def process_domain_email(self, data):
        """Process a domain email validation request"""
        try:
            result = await self.domain_email_api.validate_domain_and_email(data)
            self.logger.info(f"Successfully processed domain/email validation for {data.get('domain')}")
            return result
        except Exception as e:
            self.logger.error(f"Error processing domain/email validation: {str(e)}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage, callback):
        """Process received message"""
        async with message.process():
            try:
                # Decode message body
                body = json.loads(message.body.decode())
                self.logger.info(f"Received message: {body}")
                
                # Process message using callback
                await callback(body)
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode message: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")

    async def start_consuming(self, callback):
        """Start consuming messages"""
        try:
            self.logger.info("Starting to consume messages...")
            queue = await self.connect()
            
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.process_message(message, callback)
                    
        except Exception as e:
            self.logger.error(f"Error in consumer: {str(e)}")
            raise
        finally:
            await self.close()

    async def close(self):
        """Close connections"""
        if self.connection:
            await self.connection.close()
            self.logger.info("Closed RabbitMQ connection")
        
        await self.leak_check_api.close()
        await self.domain_email_api.close()
