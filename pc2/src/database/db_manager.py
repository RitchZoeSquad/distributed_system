import psycopg2
from psycopg2.extras import DictCursor, execute_values
from contextlib import contextmanager
from config import Config
from utils.logger import Logger
import json
from datetime import datetime
from typing import Dict, Any, List
import backoff

class DatabaseManager:
    def __init__(self):
        self.config = Config.DB_CONFIG
        self.logger = Logger('database')
        self.pool = self.create_pool()

    def create_pool(self):
        return psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host='185.249.196.192',
            database='business_db',
            user='zoeman',
            password='TestingPurposes99!!!',
            port=5432
        )

    @contextmanager
    def get_cursor(self):
        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                yield cursor
                conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            self.pool.putconn(conn)

    async def insert_business(self, data: Dict[str, Any]) -> int:
        query = """
            INSERT INTO businesses 
            (business_id, name, address, phone, processed_date, processed_by, status)
            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s, %s)
            ON CONFLICT (business_id) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                address = EXCLUDED.address,
                phone = EXCLUDED.phone,
                processed_date = CURRENT_DATE,
                processed_by = EXCLUDED.processed_by,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        try:
            self.logger.info(f"Inserting business data for: {data.get('business_id', 'unknown')}")
            with self.get_cursor() as cursor:
                cursor.execute(query, (
                    data['business_id'],
                    data['name'],
                    data['address'],
                    data['phone'],
                    Config.PC_ID,
                    'processed'
                ))
                result = cursor.fetchone()[0]
                self.logger.info(f"Successfully inserted business data for: {data.get('business_id', 'unknown')}")
                return result
        except Exception as e:
            self.logger.error(f"Error inserting business: {str(e)}")
            raise

    async def get_daily_processing_count(self) -> int:
        query = """
            SELECT COUNT(*) 
            FROM businesses 
            WHERE processed_date = CURRENT_DATE 
            AND processed_by = %s
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (Config.PC_ID,))
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error getting daily processing count: {str(e)}")
            raise

    async def cleanup_old_records(self, days: int = 30):
        query = """
            DELETE FROM businesses 
            WHERE processed_date < CURRENT_DATE - interval '%s days'
            AND processed_by = %s
            AND status = 'processed'
        """
        try:
            self.logger.info(f"Cleaning up records older than {days} days")
            with self.get_cursor() as cursor:
                cursor.execute(query, (days, Config.PC_ID))
                self.logger.info("Successfully cleaned up old records")
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {str(e)}")
            raise