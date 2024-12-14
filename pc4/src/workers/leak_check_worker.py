import aio_pika
import json
import asyncio
from config import Config
from api.leak_check_api import LeakCheckAPI
from database.db_manager import DatabaseManager
from utils.logger import Logger

class LeakCheckWorker:
    def __init__(self):
        self.logger = Logger('leak_check_worker')
        self.leak_check_api = LeakCheckAPI()
        self.db = DatabaseManager()
        self.connection = None
        self.channel = None
        self.queue_name = Config.RABBITMQ_CONFIG['queues']['leak_check']

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            # Create connection
            self.connection = await aio_pika.connect_robust(
                host=Config.RABBITMQ_CONFIG['host'],
                port=Config.RABBITMQ_CONFIG['port'],
                login=Config.RABBITMQ_CONFIG['user'],
                password=Config.RABBITMQ_CONFIG['password'],
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue
            queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )
            
            self.logger.info("Connected to RabbitMQ")
            return queue
            
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def process_message(self, message: aio_pika.IncomingMessage):
        """Process received message"""
        async with message.process():
            try:
                # Decode message body
                body = json.loads(message.body.decode())
                self.logger.info(f"Received message: {body}")
                
                # Extract data from message
                email = body.get('email')
                if not email:
                    self.logger.error("No email provided in message")
                    return
                
                # Process the leak check request
                leak_results = await self.leak_check_api.check_email_leaks(email)
                
                # Store results in database
                await self.db.insert_email_leak_check(leak_results)
                
                self.logger.info(f"Successfully processed leak check for {email}")
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode message: {str(e)}")
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")

    async def start(self):
        """Start the worker"""
        try:
            # Connect to RabbitMQ
            queue = await self.connect()
            
            # Start consuming messages
            self.logger.info(f"Starting to consume messages from {self.queue_name}")
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    await self.process_message(message)
                    
        except Exception as e:
            self.logger.error(f"Worker error: {str(e)}")
            raise
        finally:
            # Clean up
            if self.connection:
                await self.connection.close()
                self.logger.info("Closed RabbitMQ connection")