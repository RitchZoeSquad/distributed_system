import psycopg2
from psycopg2.extras import DictCursor, execute_values
from contextlib import contextmanager
from config import Config
from utils.logger import Logger
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
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

    async def insert_domain_email_validation(self, data: Dict[str, Any]) -> int:
        """Insert domain and email validation results"""
        query = """
            INSERT INTO domain_email_data (
                business_id,
                domain,
                organization_info,
                emails,
                validation_status,
                processed_date,
                processed_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (business_id) DO UPDATE SET
                domain = EXCLUDED.domain,
                organization_info = EXCLUDED.organization_info,
                emails = EXCLUDED.emails,
                validation_status = EXCLUDED.validation_status,
                processed_date = EXCLUDED.processed_date,
                processed_by = EXCLUDED.processed_by,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        try:
            # Determine validation status based on data
            validation_status = 'valid' if data.get('emails') else 'invalid'
            
            with self.get_cursor() as cursor:
                cursor.execute(query, (
                    data.get('business_id'),
                    data.get('domain'),
                    json.dumps(data.get('organization', {})),
                    json.dumps(data.get('emails', [])),
                    validation_status,
                    data.get('processed_date'),
                    data.get('processed_by')
                ))
                result = cursor.fetchone()[0]
                self.logger.info(f"Successfully inserted domain/email validation for: {data.get('business_id')}")
                return result
                
        except Exception as e:
            self.logger.error(f"Error inserting domain/email validation: {str(e)}")
            raise

    async def get_domain_email_validation(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve domain and email validation results for a business"""
        query = """
            SELECT 
                business_id,
                domain,
                organization_info,
                emails,
                validation_status,
                processed_date,
                processed_by,
                created_at,
                updated_at
            FROM domain_email_data
            WHERE business_id = %s
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (business_id,))
                if cursor.rowcount > 0:
                    row = cursor.fetchone()
                    return {
                        'business_id': row['business_id'],
                        'domain': row['domain'],
                        'organization': row['organization_info'],
                        'emails': row['emails'],
                        'validation_status': row['validation_status'],
                        'processed_date': row['processed_date'].isoformat(),
                        'processed_by': row['processed_by'],
                        'created_at': row['created_at'].isoformat(),
                        'updated_at': row['updated_at'].isoformat()
                    }
                return None
                
        except Exception as e:
            self.logger.error(f"Error retrieving domain/email validation: {str(e)}")
            raise

    async def insert_phone_validation(self, data: Dict[str, Any]) -> int:
        query = """
            INSERT INTO phone_validation 
            (business_id, phone, validation_status, validation_details, 
             processed_date, processed_by)
            VALUES (%s, %s, %s, %s, CURRENT_DATE, %s)
            ON CONFLICT (business_id) 
            DO UPDATE SET 
                phone = EXCLUDED.phone,
                validation_status = EXCLUDED.validation_status,
                validation_details = EXCLUDED.validation_details,
                processed_date = CURRENT_DATE,
                processed_by = EXCLUDED.processed_by,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        try:
            self.logger.info(f"Inserting phone validation for business: {data['business_id']}")
            with self.get_cursor() as cursor:
                cursor.execute(query, (
                    data['business_id'],
                    data['phone'],
                    data.get('validation_status', 'unknown'),
                    json.dumps(data.get('validation_details', {})),
                    Config.PC_ID
                ))
                result = cursor.fetchone()[0]
                self.logger.info(f"Successfully inserted phone validation for: {data['business_id']}")
                return result
        except Exception as e:
            self.logger.error(f"Error inserting phone validation: {str(e)}")
            raise

    async def get_validation_stats(self) -> Dict[str, int]:
        query = """
            SELECT 
                COUNT(*) filter (where processed_date = CURRENT_DATE) as today_count,
                COUNT(*) filter (where domain_status = 'valid') as valid_domains,
                COUNT(*) filter (where email_status = 'valid') as valid_emails,
                COUNT(*) filter (where validation_status = 'valid') as valid_phones
            FROM (
                SELECT 
                    processed_date, 
                    domain_status, 
                    email_status, 
                    NULL as validation_status
                FROM domain_email_data
                WHERE processed_by = %s
                UNION ALL
                SELECT 
                    processed_date,
                    NULL as domain_status,
                    NULL as email_status,
                    validation_status
                FROM phone_validation
                WHERE processed_by = %s
            ) combined
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (Config.PC_ID, Config.PC_ID))
                return dict(cursor.fetchone())
        except Exception as e:
            self.logger.error(f"Error getting validation stats: {str(e)}")
            raise

    async def insert_email_leak_check(self, data: Dict[str, Any]) -> int:
        """Insert email leak check results"""
        query = """
            INSERT INTO email_leak_data (
                email,
                total_leaks,
                has_password_leak,
                dehashed_results,
                leakcheck_results
            ) VALUES (
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (email) DO UPDATE SET
                total_leaks = EXCLUDED.total_leaks,
                has_password_leak = EXCLUDED.has_password_leak,
                dehashed_results = EXCLUDED.dehashed_results,
                leakcheck_results = EXCLUDED.leakcheck_results,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, (
                    data['email'],
                    data['total_leaks'],
                    data['has_password_leak'],
                    json.dumps(data['dehashed_results']),
                    json.dumps(data['leakcheck_results'])
                ))
                result = cursor.fetchone()[0]
                self.logger.info(f"Successfully inserted leak check for email: {data['email']}")
                return result
        except Exception as e:
            self.logger.error(f"Error inserting leak check data: {str(e)}")
            raise