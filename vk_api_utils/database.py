"""
Database connection module with environment detection.
Automatically detects if running on EC2 or local machine and uses appropriate connection.
"""

import os
import json
import socket
import psycopg2
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy import create_engine
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


def detect_environment() -> str:
    """
    Detect the current environment (EC2 or local).

    Returns:
        'ec2' if running on EC2, 'local' otherwise
    """
    # Check if we're on EC2 by looking for EC2 metadata or specific markers

    # Method 1: Check for EC2 metadata endpoint
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        result = sock.connect_ex(('169.254.169.254', 80))
        sock.close()
        if result == 0:
            return 'ec2'
    except:
        pass

    # Method 2: Check hostname
    hostname = socket.gethostname().lower()
    if 'ec2' in hostname or 'ip-' in hostname or 'aws' in hostname:
        return 'ec2'

    # Method 3: Check for specific environment variable
    if os.environ.get('VK_ENV') == 'EC2':
        return 'ec2'

    # Method 4: Check if we're on Windows with Administrator user (EC2 default)
    if os.name == 'nt' and os.environ.get('USERNAME') == 'Administrator':
        return 'ec2'

    return 'local'


def get_database_config() -> Dict[str, any]:
    """
    Get database configuration based on environment.
    Priority: Environment vars > Config file > Auto-detection

    Returns:
        Dictionary with connection parameters
    """

    # 1. Try environment variables first (for AWS ECS/Lambda)
    if os.environ.get('DB_PASSWORD'):
        config = {
            'host': os.environ.get('DB_HOST', 'datauploader-instance-1.ci6sgcrhrg7k.us-west-1.rds.amazonaws.com'),
            'port': int(os.environ.get('DB_PORT', '5432')),
            'database': os.environ.get('DB_NAME', 'data_uploader'),
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD')
        }
        logger.info("Using database config from environment variables")
        return config

    # 2. Try local config file
    config_path = Path.home() / '.vk' / 'db_config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config = {
                    'host': file_config.get('host', 'localhost'),
                    'port': int(file_config.get('port', '5433')),
                    'database': file_config.get('database', 'data_uploader'),
                    'user': file_config.get('user', 'postgres'),
                    'password': file_config['password']
                }
                # Override host/port based on environment detection if not explicitly set
                if file_config.get('host') == 'localhost' or not file_config.get('host'):
                    env = detect_environment()
                    if env == 'ec2':
                        config['host'] = 'datauploader-instance-1.ci6sgcrhrg7k.us-west-1.rds.amazonaws.com'
                        config['port'] = 5432
                    else:
                        config['host'] = 'localhost'
                        config['port'] = 5433

                logger.info(f"Using database config from {config_path}")
                return config
        except Exception as e:
            logger.warning(f"Could not read config file: {e}")

    # 3. Auto-detect based on environment
    env = detect_environment()

    if env == 'ec2':
        # EC2 configuration - direct RDS connection
        config = {
            'host': 'datauploader-instance-1.ci6sgcrhrg7k.us-west-1.rds.amazonaws.com',
            'port': 5432,
            'database': 'data_uploader',
            'user': 'postgres',
            'password': 'sPeGSSFX9jF2EN8mAv47zWiwG9za/Zaq'
        }
        logger.info("🖥️  Detected EC2 environment - using direct RDS connection")
    else:
        # Local development - use SSH tunnel
        config = {
            'host': 'localhost',
            'port': 5433,
            'database': 'data_uploader',
            'user': 'postgres',
            'password': 'sPeGSSFX9jF2EN8mAv47zWiwG9za/Zaq'
        }
        logger.info("💻 Detected local environment - using SSH tunnel (port 5433)")

    return config


def test_connection(config: Optional[Dict] = None) -> bool:
    """
    Test database connection with given or auto-detected config.

    Args:
        config: Optional database configuration dict

    Returns:
        True if connection successful, False otherwise
    """
    if config is None:
        config = get_database_config()

    try:
        conn = psycopg2.connect(**config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        conn.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False


def get_connection():
    """
    Get a database connection with auto-detected configuration.

    Returns:
        psycopg2 connection object
    """
    config = get_database_config()
    return psycopg2.connect(**config)


def get_engine():
    """
    Get SQLAlchemy engine with auto-detected configuration.

    Returns:
        SQLAlchemy engine object
    """
    config = get_database_config()
    db_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    return create_engine(db_url)


@contextmanager
def get_db_session():
    """
    Context manager for database connections.
    Automatically handles connection cleanup.

    Usage:
        with get_db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


# Legacy compatibility functions
def PGconnection():
    """Legacy PGconnection function for backward compatibility"""
    return get_engine()


def get_db_connection():
    """Legacy function returning config dict for backward compatibility"""
    return get_database_config()


if __name__ == "__main__":
    # Test the connection when run directly
    config = get_database_config()
    print(f"\n📊 Database Configuration:")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   Database: {config['database']}")
    print(f"   User: {config['user']}")

    if test_connection(config):
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
        if config['port'] == 5433:
            print("\n💡 Make sure SSH tunnel is active:")
            print("   ssh -L 5433:localhost:5432 your-bastion-server")