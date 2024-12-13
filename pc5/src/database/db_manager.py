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

    async def insert_serp_result(self, data: Dict[str, Any]) -> int:
        query = """
            INSERT INTO serp_results 
            (business_id, business_name, business_address, city, state_code,
             search_query, serp_data, processed_date, processed_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)
            ON CONFLICT (business_id) 
            DO UPDATE SET 
                business_name = EXCLUDED.business_name,
                business_address = EXCLUDED.business_address,
                search_query = EXCLUDED.search_query,
                serp_data = EXCLUDED.serp_data,
                processed_date = CURRENT_DATE,
                processed_by = EXCLUDED.processed_by,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        try:
            self.logger.info(f"Inserting SERP results for business: {data['business_name']}")
            with self.get_cursor() as cursor:
                cursor.execute(query, (
                    data.get('business_id'),
                    data.get('business_name'),
                    data.get('business_address'),
                    data.get('city'),
                    data.get('state_code'),
                    data.get('search_query'),
                    json.dumps(data.get('serp_results')),
                    Config.PC_ID
                ))
                result = cursor.fetchone()[0]
                self.logger.info(f"Successfully inserted SERP results for: {data['business_name']}")
                return result
        except Exception as e:
            self.logger.error(f"Error inserting SERP results: {str(e)}")
            raise

    async def get_daily_processing_count(self) -> int:
        query = """
            SELECT COUNT(*) 
            FROM serp_results 
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

    async def get_business_serp_results(self, business_id: str) -> Dict:
        query = """
            SELECT * FROM serp_results 
            WHERE business_id = %s
            ORDER BY updated_at DESC 
            LIMIT 1
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (business_id,))
                return dict(cursor.fetchone()) if cursor.rowcount > 0 else None
        except Exception as e:
            self.logger.error(f"Error fetching SERP results: {str(e)}")
            raise