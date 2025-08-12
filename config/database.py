import os
import pyodbc
import logging
import yaml
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        # Load secrets from secrets.yml (decrypted by Ansible Vault)
        try:
            with open('secrets.yml', 'r') as f:
                secrets = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error("secrets.yml not found. Ensure Ansible Vault has decrypted it.")
            secrets = {}

        self.host = secrets.get('db_host', os.getenv('DB_HOST', 'localhost'))
        self.port = os.getenv('DB_PORT', '1433') # Port can still be from env or default
        self.database = secrets.get('db_name', os.getenv('DB_NAME', 'SentimentDB'))
        self.username = secrets.get('db_user', os.getenv('DB_USER', 'sa'))
        self.password = secrets.get('db_password', os.getenv('DB_PASSWORD'))
        self.api_key = secrets.get('api_key', os.getenv('API_KEY'))
        
        if not self.password:
            raise ValueError("DB_PASSWORD is required and not found in secrets.yml or environment variables")
        if not self.api_key:
            raise ValueError("API_KEY is required and not found in secrets.yml or environment variables")
    
    def get_connection_string(self) -> str:
        """Get ODBC connection string"""
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TrustServerCertificate=yes;"
        )
    
    def get_connection(self) -> Optional[pyodbc.Connection]:
        """Get database connection"""
        try:
            connection_string = self.get_connection_string()
            connection = pyodbc.connect(connection_string)
            logger.info("Database connection established successfully")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()
                return result is not None
            return False
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

# Global database configuration instance
db_config = DatabaseConfig()



