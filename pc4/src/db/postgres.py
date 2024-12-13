import asyncpg
from config import Config

async def get_db_pool():
    """Create a connection pool to PostgreSQL"""
    return await asyncpg.create_pool(
        host=Config.DB_CONFIG['host'],
        port=Config.DB_CONFIG['port'],
        database=Config.DB_CONFIG['database'],
        user=Config.DB_CONFIG['user'],
        password=Config.DB_CONFIG['password'],
        min_size=5,
        max_size=20
    ) 