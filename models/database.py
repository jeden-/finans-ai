import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, max_retries=3, retry_delay=2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._connect_with_retry()
        self._init_db()

    def _connect_with_retry(self):
        retries = 0
        last_exception = None

        while retries < self.max_retries:
            try:
                logger.info(f"Attempting database connection (attempt {retries + 1}/{self.max_retries})")
                self.conn = psycopg2.connect(
                    dbname=os.environ['PGDATABASE'],
                    user=os.environ['PGUSER'],
                    password=os.environ['PGPASSWORD'],
                    host=os.environ['PGHOST'],
                    port=os.environ['PGPORT']
                )
                self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
                logger.info("Database connection established successfully")
                return
            except Exception as e:
                last_exception = e
                logger.error(f"Connection attempt {retries + 1} failed: {str(e)}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)

        raise Exception(f"Failed to connect to database after {self.max_retries} attempts: {str(last_exception)}")

    def _init_db(self):
        try:
            logger.info("Initializing database schema")
            schema_path = Path('assets/schema.sql')
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found at {schema_path}")
                
            with open(schema_path, 'r') as file:
                schema_sql = file.read()
                
            self.cursor.execute(schema_sql)
            self.conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            self.conn.rollback()
            raise

    def execute(self, query, params=None):
        try:
            logger.info(f"Executing query with params: {params}")
            self.cursor.execute(query, params)
            self.conn.commit()
            logger.info("Query executed successfully")
            return self.cursor.rowcount
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {str(e)}")
            self.conn.rollback()
            raise

    def fetch_all(self, query, params=None):
        try:
            logger.info(f"Executing fetch_all query: {query}")
            logger.debug(f"Query params: {params}")
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            logger.info(f"Query returned {len(results)} results")
            return results
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def fetch_one(self, query, params=None):
        try:
            logger.info(f"Executing fetch_one query: {query}")
            logger.debug(f"Query params: {params}")
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            logger.info(f"Query returned {'a result' if result else 'no result'}")
            return result
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
