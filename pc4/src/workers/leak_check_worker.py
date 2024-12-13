import pika
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

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                Config.RABBITMQ_CONFIG['user'],
                Config.RABBITMQ_CONFIG['password']
            )
            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_CONFIG['host'],
                port=Config.RABBITMQ_CONFIG['port'],
                credentials=credentials,
                heartbeat=600
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare the queue
            self.channel.queue_declare(
                queue=Config.RABBITMQ_CONFIG['queues']['leak_check'],
                durable=True
            )
            
            self.logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def process_message(self, email: str) -> None:
        """Process a single email leak check request"""
        try:
            # Check for leaks
            leak_results = await self.leak_check_api.check_email_leaks(email)
            
            # Store results in database
            await self.db.insert_email_leak_check(leak_results)
            
            self.logger.info(f"Successfully processed leak check for email: {email}")
            
        except Exception as e:
            self.logger.error(f"Error processing leak check for {email}: {str(e)}")

    async def callback(self, ch, method, properties, body):
        """Handle incoming messages"""
        try:
            message = json.loads(body)
            email = message.get('email')
            
            if not email:
                self.logger.error("Received message without email")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Process the message
            await self.process_message(email)
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            # Negative acknowledgment with requeue
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def start(self):
        """Start consuming messages"""
        try:
            await self.connect()
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            self.channel.basic_consume(
                queue=Config.RABBITMQ_CONFIG['queues']['leak_check'],
                on_message_callback=self.callback
            )
            
            self.logger.info("Started consuming messages")
            self.channel.start_consuming()
            
        except Exception as e:
            self.logger.error(f"Error in leak check worker: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            raise

    async def stop(self):
        """Stop the worker"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        await self.leak_check_api.close() 