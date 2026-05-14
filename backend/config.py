"""
TRAKN - Personal Expense Tracker
Database Configuration
Supports SQLite (default), MySQL, and PostgreSQL
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Database Configuration
# Change these values to match your database setup

DB_TYPE = os.environ.get('DB_TYPE', 'mysql')  # 'sqlite', 'mysql', or 'postgresql'

# The code snippet you provided is setting up configurations for SQLite and MySQL databases in a
# Python application called TRAKN - Personal Expense Tracker. Here's what each part of the code is
# doing:
# SQLite Configuration (default)
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trakn.db')

# MySQL Configuration
MYSQL_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'database': os.environ.get('MYSQL_DATABASE', 'trakn'),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'charset': 'utf8mb4'
}

# PostgreSQL Configuration
POSTGRESQL_CONFIG = {
    'host': os.environ.get('PG_HOST', 'localhost'),
    'port': int(os.environ.get('PG_PORT', 5432)),
    'database': os.environ.get('PG_DATABASE', 'trakn'),
    'user': os.environ.get('PG_USER', 'postgres'),
    'password': os.environ.get('PG_PASSWORD', '')
}

def get_database_url():
    """Get database URL based on configuration"""
    if DB_TYPE == 'mysql':
        return f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}"
    elif DB_TYPE == 'postgresql':
        return f"postgresql://{POSTGRESQL_CONFIG['user']}:{POSTGRESQL_CONFIG['password']}@{POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}/{POSTGRESQL_CONFIG['database']}"
    else:
        return f"sqlite:///{SQLITE_DB_PATH}"

def get_db_config():
    """Get database configuration dictionary"""
    if DB_TYPE == 'mysql':
        return MYSQL_CONFIG
    elif DB_TYPE == 'postgresql':
        return POSTGRESQL_CONFIG
    else:
        return {'path': SQLITE_DB_PATH}

# Print configuration on load (for debugging)
print(f"\n{'='*50}")
print(f"TRAKN Database Configuration")
print(f"{'='*50}")
print(f"Database Type: {DB_TYPE.upper()}")
if DB_TYPE == 'mysql':
    print(f"MySQL Host: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    print(f"MySQL Database: {MYSQL_CONFIG['database']}")
    print(f"MySQL User: {MYSQL_CONFIG['user']}")
elif DB_TYPE == 'postgresql':
    print(f"PostgreSQL Host: {POSTGRESQL_CONFIG['host']}:{POSTGRESQL_CONFIG['port']}")
    print(f"PostgreSQL Database: {POSTGRESQL_CONFIG['database']}")
    print(f"PostgreSQL User: {POSTGRESQL_CONFIG['user']}")
else:
    print(f"SQLite Path: {SQLITE_DB_PATH}")
print(f"{'='*50}\n")
