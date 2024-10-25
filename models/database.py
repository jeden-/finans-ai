import os
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self, max_retries=3, retry_delay=2):
        if self.initialized:
            return
            
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.pool = None
        self._create_pool()
        self._init_db()
        self.initialized = True

    def _create_pool(self):
        retries = 0
        last_exception = None

        while retries < self.max_retries:
            try:
                logger.info(f"Creating connection pool (attempt {retries + 1}/{self.max_retries})")
                self.pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,
                    dbname=os.environ['PGDATABASE'],
                    user=os.environ['PGUSER'],
                    password=os.environ['PGPASSWORD'],
                    host=os.environ['PGHOST'],
                    port=os.environ['PGPORT']
                )
                logger.info("Connection pool created successfully")
                return
            except Exception as e:
                last_exception = e
                logger.error(f"Pool creation attempt {retries + 1} failed: {str(e)}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)

        raise Exception(f"Failed to create connection pool after {self.max_retries} attempts: {str(last_exception)}")

    def _get_connection(self):
        """Get a connection from the pool."""
        try:
            conn = self.pool.getconn()
            conn.autocommit = False  # Ensure explicit transaction control
            return conn
        except Exception as e:
            logger.error(f"Error getting connection from pool: {str(e)}")
            raise

    def _return_connection(self, conn):
        """Return a connection to the pool."""
        try:
            self.pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {str(e)}")

    def _init_db(self):
        """Initialize database schema."""
        conn = None
        try:
            logger.info("Initializing database schema")
            schema_path = Path('assets/schema.sql')
            
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found at {schema_path}")
                
            with open(schema_path, 'r') as file:
                schema_sql = file.read()
            
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._return_connection(conn)

    def execute(self, query, params=None):
        """Execute a query with parameters."""
        conn = None
        try:
            logger.info(f"Executing query with params: {params}")
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rowcount = cur.rowcount
            conn.commit()
            logger.info(f"Query executed successfully, affected rows: {rowcount}")
            return rowcount
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._return_connection(conn)

    def fetch_all(self, query, params=None):
        """Fetch all rows from a query."""
        conn = None
        try:
            logger.info(f"Executing fetch_all query: {query}")
            logger.debug(f"Query params: {params}")
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
            conn.commit()
            logger.info(f"Query returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._return_connection(conn)

    def fetch_one(self, query, params=None):
        """Fetch a single row from a query."""
        conn = None
        try:
            logger.info(f"Executing fetch_one query: {query}")
            logger.debug(f"Query params: {params}")
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchone()
            conn.commit()
            logger.info(f"Query returned {'a result' if result else 'no result'}")
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._return_connection(conn)

    def close(self):
        """Close the connection pool."""
        try:
            if self.pool:
                self.pool.closeall()
                logger.info("Connection pool closed")
        except Exception as e:
            logger.error(f"Error closing connection pool: {str(e)}")
