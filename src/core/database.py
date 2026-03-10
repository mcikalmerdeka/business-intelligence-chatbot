"""Database connection and query execution"""

import psycopg2
import streamlit as st
from typing import Optional, List, Tuple
from config import logger_db

logger = logger_db


class DatabaseConnection:
    """Manage database connections and operations"""

    def __init__(self, dsn: Optional[str] = None, *, host: str = "", database: str = "", user: str = "", password: str = "", port: str = "5432"):
        """
        Accepts either a full DSN/URL (preferred for Neon) or individual params.

        Args:
            dsn: Full connection URI, e.g. postgresql://user:pass@host/db?sslmode=require
            host: Database host (ignored when dsn is provided)
            database: Database name (ignored when dsn is provided)
            user: Database user (ignored when dsn is provided)
            password: Database password (ignored when dsn is provided)
            port: Database port (ignored when dsn is provided)
        """
        self.dsn = dsn
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port

    def connect(self) -> Optional[psycopg2.extensions.connection]:
        try:
            if self.dsn:
                logger.info("Connecting via DATABASE_URL")
                connection = psycopg2.connect(self.dsn)
            else:
                logger.info(f"Connecting to database {self.database} at {self.host}:{self.port}")
                connection = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port,
                )
            logger.info("Database connection established")
            return connection
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            st.error(f"Error with database connection: {e}")
            return None

    def test_connection(self) -> bool:
        label = self.database or "neon"
        logger.info(f"Testing connection to database {label}")
        connection = self.connect()
        if connection:
            connection.close()
            logger.info(f"Connection test successful for database {label}")
            st.success(f"Connected to database {label} successfully!")
            return True
        logger.warning(f"Connection test failed for database {label}")
        return False


def execute_sql_query(db_connection: DatabaseConnection, query: str) -> Optional[List[Tuple]]:
    """
    Execute an SQL query and return the result
    
    Args:
        db_connection: DatabaseConnection instance
        query: SQL query string
        
    Returns:
        List of tuples containing query results, or None if error
    """
    logger.debug(f"Executing SQL query: {query[:100]}...")
    connection = db_connection.connect()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Query executed successfully, returned {len(rows)} rows")
            return rows
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            st.error(f"Error executing query: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
            logger.debug("Database connection closed")
    return None
