import pika
import json
import asyncio
from config import Config
from utils.logger import Logger
from typing import Callable, Any, Dict
import backoff
from datetime import datetime

class QueueConsumer:
    def __init__(self):
        self.config = Config.RABBITMQ_CONFIG
        self.logger = Logger('queue_consumer')
        self.connections = {}
        self.channels = {}
        self.processing = False

    @backoff.on_exception(
        backoff.expo,
        (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosedByBroker),
        max_tries=5
    )
    def connect(self, queue_type: str):
        if queue_type not in self.connections or self.connections[queue_type].is_closed:
            credentials = pika.PlainCredentials(
                self.config['user'],
                self.config['password']
            )
            parameters = pika.ConnectionParameters(
                host=self.config['host'],
                port=self.config['port'],
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=5,
                client_properties={
                    'connection_name': f'pc4_{queue_type}_worker'
                }
            )
            self.connections[queue_type] = pika.BlockingConnection(parameters)
            self.channels[queue_type] = self.connections[queue_type].channel()
            
            # Declare the main queue
            queue_name = self.config['queues'][queue_type]
            self.channels[queue_type].queue_declare(
                queue=queue_name,
                durable=True
            )
            
            # Declare the dead letter queue
            dlq_name = f"{queue_name}_dlq"
            self.channels[queue_type].queue_declare(
                queue=dlq_name,
                durable=True
            )
            
            # Set QoS
            self.channels[queue_type].basic_qos(prefetch_count=1)
            self.logger.info(f"Successfully connected to RabbitMQ for {queue_type} queue")

    async def process_message(self, queue_type: str, callback: Callable, ch: Any, method: Any, properties: Any, body: bytes):
        try:
            message_id = properties.message_id if properties.message_id else 'unknown'
            self.logger.info(f"Processing {queue_type} message {message_id}")
            
            data = json.loads(body)
            await callback(data)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.debug(f"Successfully processed {queue_type} message: {message_id}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {queue_type} message: {str(e)}")
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            self.logger.error(f"Error processing {queue_type} message: {str(e)}")
            retry_count = properties.headers.get('x-death', [{}])[0].get('count', 0) if properties.headers else 0
            requeue = retry_count < 3
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=requeue)
            
            if not requeue:
                self.logger.warning(f"Message {message_id} exceeded max retries, moving to DLQ")

    async def start_consuming(self, queue_type: str, callback: Callable):
        self.processing = True
        
        def message_handler(ch, method, properties, body):
            if self.processing:
                asyncio.create_task(
                    self.process_message(queue_type, callback, ch, method, properties, body)
                )

        while self.processing:
            try:
                self.connect(queue_type)
                queue_name = self.config['queues'][queue_type]
                self.channels[queue_type].basic_consume(
                    queue=queue_name,
                    on_message_callback=message_handler
                )
                self.logger.info(f"Started consuming from {queue_name}")
                self.channels[queue_type].start_consuming()
                
            except (pika.exceptions.AMQPConnectionError, 
                    pika.exceptions.ChannelClosedByBroker) as e:
                self.logger.error(f"Connection error for {queue_type}: {str(e)}")
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Unexpected error for {queue_type}: {str(e)}")
                await asyncio.sleep(5)

    async def stop_consuming(self, queue_type: str = None):
        self.processing = False
        if queue_type:
            if queue_type in self.channels:
                self.channels[queue_type].stop_consuming()
            if queue_type in self.connections and not self.connections[queue_type].is_closed:
                self.connections[queue_type].close()
        else:
            for qt in self.channels:
                self.channels[qt].stop_consuming()
            for qt in self.connections:
                if not self.connections[qt].is_closed:
                    self.connections[qt].close()

    def close(self):
        for qt in self.connections:
            if not self.connections[qt].is_closed:
                self.connections[qt].close()
        self.logger.info("Closed all RabbitMQ connections")