import asyncpg
from config import Config
from utils.logger import Logger

logger = Logger('postgres')

async def get_db_pool():
    """Create a connection pool to PostgreSQL"""
    try:
        return await asyncpg.create_pool(
            host=Config.DB_CONFIG['host'],
            port=Config.DB_CONFIG['port'],
            database=Config.DB_CONFIG['database'],
            user=Config.DB_CONFIG['user'],
            password=Config.DB_CONFIG['password'],
            min_size=5,
            max_size=20
        )
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise 