import pika
import json
import asyncio
from config import Config
from utils.logger import Logger
from typing import Callable, Any
import backoff
from datetime import datetime

class QueueConsumer:
    def __init__(self):
        self.logger = Logger('queue_consumer')
        self.connection = None
        self.channel = None
        self.processing = False

    @backoff.on_exception(
        backoff.expo,
        (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker),
        max_tries=5
    )
    def connect(self):
        if not self.connection or self.connection.is_closed:
            credentials = pika.PlainCredentials(
                username='zoeman',
                password='TestingPurposes9!'
            )
            parameters = pika.ConnectionParameters(
                host='185.249.196.192',
                port=5672,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5,
                virtual_host='/'
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare the SERP queue
            self.channel.queue_declare(
                queue='serp_queue',
                durable=True
            )
            
            # Declare the dead letter queue
            self.channel.queue_declare(
                queue='serp_queue_dlq',
                durable=True
            )
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            self.logger.info("Successfully connected to RabbitMQ")

    async def process_message(self, callback: Callable, ch: Any, method: Any, properties: Any, body: bytes):
        try:
            message_id = properties.message_id if properties.message_id else 'unknown'
            self.logger.info(f"Processing SERP message {message_id}")
            
            data = json.loads(body)
            await callback(data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.debug(f"Successfully processed SERP message: {message_id}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in message: {str(e)}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            retry_count = properties.headers.get('x-death', [{}])[0].get('count', 0) if properties.headers else 0
            requeue = retry_count < 3
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=requeue)
            
            if not requeue:
                self.logger.warning(f"Message {message_id} exceeded max retries, moving to DLQ")

    async def start_consuming(self, callback: Callable):
        self.processing = True
        
        def message_handler(ch, method, properties, body):
            if self.processing:
                asyncio.create_task(self.process_message(callback, ch, method, properties, body))

        while self.processing:
            try:
                self.connect()
                self.channel.basic_consume(
                    queue='serp_queue',
                    on_message_callback=message_handler
                )
                self.logger.info("Started consuming from SERP queue")
                self.channel.start_consuming()
                
            except (pika.exceptions.AMQPConnectionError, 
                    pika.exceptions.ChannelClosedByBroker) as e:
                self.logger.error(f"Connection error: {str(e)}")
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                await asyncio.sleep(5)

    async def stop_consuming(self):
        self.processing = False
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        self.logger.info("Stopped consuming messages")

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.logger.info("Closed RabbitMQ connection")