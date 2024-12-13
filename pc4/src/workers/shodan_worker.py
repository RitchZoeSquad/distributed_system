import json
import asyncio
from typing import Dict, Any
import aio_pika
from config import Config
from api.shodan_api import ShodanAPI
from cache.shodan_cache import ShodanCache
from utils.logger import Logger
from db.postgres import get_db_pool

class ShodanWorker:
    def __init__(self):
        self.logger = Logger('shodan_worker')
        self.shodan_api = ShodanAPI()
        self.cache = ShodanCache()
        self.db_pool = None

    async def process_search_message(self, message: Dict[str, Any]):
        """Process a search request message"""
        try:
            query = message.get('query')
            if not query:
                return

            # Check cache first
            cached_results = await self.cache.get_search_results(query)
            if cached_results:
                return cached_results

            # Perform search
            results = await self.shodan_api.search_host(query)
            
            # Cache results
            await self.cache.set_search_results(query, results)

            # Store in database
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    await self.shodan_api.write_to_database(results, conn)

            return results

        except Exception as e:
            self.logger.error(f"Error processing search message: {str(e)}")
            raise

    async def start(self):
        """Start the worker"""
        try:
            # Connect to RabbitMQ
            connection = await aio_pika.connect_robust(
                f"amqp://{Config.RABBITMQ_CONFIG['user']}:{Config.RABBITMQ_CONFIG['password']}"
                f"@{Config.RABBITMQ_CONFIG['host']}:{Config.RABBITMQ_CONFIG['port']}/"
            )

            # Initialize database pool
            self.db_pool = await get_db_pool()

            # Create channel
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)

            # Declare queues
            search_queue = await channel.declare_queue(
                "shodan_search_queue",
                durable=True
            )

            async def process_message(message):
                async with message.process():
                    try:
                        msg_data = json.loads(message.body.decode())
                        await self.process_search_message(msg_data)
                    except Exception as e:
                        self.logger.error(f"Message processing error: {str(e)}")
                        # Reject message and requeue
                        await message.reject(requeue=True)

            # Start consuming
            await search_queue.consume(process_message)

            try:
                await asyncio.Future()  # run forever
            finally:
                await connection.close()
                await self.cache.close()
                await self.shodan_api.close()
                await self.db_pool.close()

        except Exception as e:
            self.logger.error(f"Worker error: {str(e)}")
            raise

    async def stop(self):
        """Stop the worker"""
        await self.cache.close()
        await self.shodan_api.close()
        if self.db_pool:
            await self.db_pool.close() 