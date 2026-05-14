"""
TRAKN - Personal Expense Tracker
Database Models and Schema - Multi-database Support
Supports SQLite, MySQL, and PostgreSQL
"""

import os
import uuid
import hashlib
from datetime import datetime
from contextlib import contextmanager

# Import configuration
from config import DB_TYPE, SQLITE_DB_PATH, MYSQL_CONFIG, POSTGRESQL_CONFIG

# ==================== DB CONNECTION ====================

if DB_TYPE == 'mysql':
    import pymysql
    pymysql.install_as_MySQLdb()

    def get_db_connection():
        conn = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            charset=MYSQL_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn

elif DB_TYPE == 'postgresql':
    import psycopg2
    from psycopg2.extras import DictCursor

    def get_db_connection():
        conn = psycopg2.connect(
            host=POSTGRESQL_CONFIG['host'],
            port=POSTGRESQL_CONFIG['port'],
            user=POSTGRESQL_CONFIG['user'],
            password=POSTGRESQL_CONFIG['password'],
            database=POSTGRESQL_CONFIG['database']
        )
        conn.autocommit = False
        return conn

else:
    import sqlite3

    def get_db_connection():
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


# ── Shorthand for placeholder style ──────────────────────────
def ph():
    """Return the correct placeholder character for the active DB."""
    return '%s' if DB_TYPE in ('mysql', 'postgresql') else '?'


def placeholders(n):
    """Return n comma-separated placeholders, e.g. '?, ?, ?'."""
    p = ph()
    return ', '.join([p] * n)


# ==================== INIT DB ====================

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()

        if DB_TYPE == 'mysql':
            # ── MySQL ──────────────────────────────────────────
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    avatar TEXT,
                    phone VARCHAR(50),
                    role ENUM('user','admin') DEFAULT 'user',
                    status ENUM('active','inactive') DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    type ENUM('income','expense') NOT NULL,
                    category VARCHAR(100),
                    date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_date (date),
                    INDEX idx_type (type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    alert_threshold INT DEFAULT 80,
                    period VARCHAR(20) DEFAULT 'monthly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_category (user_id, category),
                    INDEX idx_user_id (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    balance DECIMAL(15,2) DEFAULT 0,
                    currency VARCHAR(10) DEFAULT 'INR',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recurring (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255),
                    amount DECIMAL(15,2),
                    type ENUM('income','expense'),
                    frequency VARCHAR(50),
                    category VARCHAR(100),
                    start_date DATE,
                    end_date DATE,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_posted DATE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255),
                    target_amount DECIMAL(15,2),
                    current_amount DECIMAL(15,2) DEFAULT 0,
                    target_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(255),
                    value DECIMAL(15,2),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS liabilities (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INT NOT NULL,
                    name VARCHAR(255),
                    amount DECIMAL(15,2),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

        elif DB_TYPE == 'postgresql':
            # ── PostgreSQL ─────────────────────────────────────
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    avatar TEXT,
                    phone VARCHAR(50),
                    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user','admin')),
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','inactive')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('income','expense')),
                    category VARCHAR(100),
                    date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_user ON transactions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(type)')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category VARCHAR(100) NOT NULL,
                    amount DECIMAL(15,2) NOT NULL,
                    alert_threshold INTEGER DEFAULT 80,
                    period VARCHAR(20) DEFAULT 'monthly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, category)
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    balance DECIMAL(15,2) DEFAULT 0,
                    currency VARCHAR(10) DEFAULT 'INR',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recurring (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    amount DECIMAL(15,2),
                    type VARCHAR(20) CHECK (type IN ('income','expense')),
                    frequency VARCHAR(50),
                    category VARCHAR(100),
                    start_date DATE,
                    end_date DATE,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_posted DATE
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255),
                    target_amount DECIMAL(15,2),
                    current_amount DECIMAL(15,2) DEFAULT 0,
                    target_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255),
                    value DECIMAL(15,2)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS liabilities (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(255),
                    amount DECIMAL(15,2)
                )
            ''')

        else:
            # ── SQLite ─────────────────────────────────────────
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    avatar TEXT,
                    phone TEXT,
                    role TEXT DEFAULT 'user',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income','expense')),
                    category TEXT,
                    date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    alert_threshold INTEGER DEFAULT 80,
                    period TEXT DEFAULT 'monthly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, category)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    balance REAL DEFAULT 0,
                    currency TEXT DEFAULT 'INR',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # ── FIXED: These 4 tables were missing from SQLite init ──
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recurring (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    amount REAL,
                    type TEXT,
                    frequency TEXT,
                    category TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    notes TEXT,
                    is_active INTEGER DEFAULT 1,
                    last_posted TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    target_amount REAL,
                    current_amount REAL DEFAULT 0,
                    target_date TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT,
                    value REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS liabilities (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT,
                    amount REAL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_budgets_user_id ON budgets(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)')

        conn.commit()
        print(f"✓ {DB_TYPE.upper()} database initialized successfully!")


# ==================== DEFAULT ADMIN ====================

def create_default_admin():
    with get_db() as conn:
        cursor = conn.cursor()
        p = ph()
        cursor.execute(f"SELECT id FROM users WHERE email = {p}", ('admin@trakn.com',))
        if not cursor.fetchone():
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute(
                f'INSERT INTO users (name, email, password, role, status) VALUES ({placeholders(5)})',
                ('Admin', 'admin@trakn.com', password_hash, 'admin', 'active')
            )
            conn.commit()
            print("✓ Default admin user created!")
            print("  Email: admin@trakn.com")
            print("  Password: admin123")


# ==================== USER OPERATIONS ====================

def create_user(name, email, password, role='user', phone=''):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f'INSERT INTO users (name, email, password, role, phone) VALUES ({placeholders(5)})',
                (name, email, password_hash, role, phone)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error creating user: {e}")
            return None


def get_user_by_email(email):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM users WHERE email = {ph()}', (email,))
        result = cursor.fetchone()
        return dict(result) if result else None


def get_user_by_id(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM users WHERE id = {ph()}', (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None


def update_user(user_id, **kwargs):
    allowed = ['name', 'email', 'phone', 'avatar']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    p = ph()
    set_clause = ', '.join([f"{k} = {p}" for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = {p}',
            values
        )
        conn.commit()
        return cursor.rowcount > 0


def verify_password(email, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = get_user_by_email(email)
    if user and user['password'] == password_hash:
        return user
    return None


def get_all_users():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, role, status, created_at FROM users ORDER BY created_at DESC')
        return [dict(r) for r in cursor.fetchall()]


def is_admin(user_id):
    user = get_user_by_id(user_id)
    return user and user['role'] == 'admin'


def update_user_status(user_id, status):
    user = get_user_by_id(user_id)
    if user and user['role'] == 'admin':
        return False, "Admin users cannot be deactivated"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE users SET status = {ph()}, updated_at = CURRENT_TIMESTAMP WHERE id = {ph()}',
            (status, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0, "Status updated successfully"


def update_user_role(user_id, role):
    user = get_user_by_id(user_id)
    if user and user['role'] == 'admin':
        return False, "Admin role cannot be changed"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE users SET role = {ph()}, updated_at = CURRENT_TIMESTAMP WHERE id = {ph()}',
            (role, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0, "Role updated successfully"


def delete_user(user_id):
    user = get_user_by_id(user_id)
    if user and user['role'] == 'admin':
        return False, "Admin users cannot be deleted"
    p = ph()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM transactions WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM budgets WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM accounts WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM recurring WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM goals WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM assets WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM liabilities WHERE user_id = {p}', (user_id,))
        cursor.execute(f'DELETE FROM users WHERE id = {p}', (user_id,))
        conn.commit()
        return cursor.rowcount > 0, "User deleted successfully"


def count_admins():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
        result = cursor.fetchone()
        return dict(result)['count'] if result else 0


def update_password(user_id, password_hash):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE users SET password = {ph()}, updated_at = CURRENT_TIMESTAMP WHERE id = {ph()}',
            (password_hash, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ==================== TRANSACTION OPERATIONS ====================

def create_transaction(user_id, title, amount, trans_type, category, date, notes=None):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'INSERT INTO transactions (user_id, title, amount, type, category, date, notes) VALUES ({placeholders(7)})',
            (user_id, title, amount, trans_type, category, date, notes)
        )
        conn.commit()
        return cursor.lastrowid


def get_transactions(user_id, filters=None):
    p = ph()
    query  = f'SELECT * FROM transactions WHERE user_id = {p}'
    params = [user_id]

    if filters:
        if filters.get('type'):
            query += f' AND type = {p}'
            params.append(filters['type'])
        if filters.get('category'):
            query += f' AND category = {p}'
            params.append(filters['category'])
        if filters.get('start_date'):
            query += f' AND date >= {p}'
            params.append(filters['start_date'])
        if filters.get('end_date'):
            query += f' AND date <= {p}'
            params.append(filters['end_date'])

    query += ' ORDER BY date DESC, created_at DESC'

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def get_transaction_by_id(transaction_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM transactions WHERE id = {ph()} AND user_id = {ph()}',
            (transaction_id, user_id)
        )
        result = cursor.fetchone()
        return dict(result) if result else None


def update_transaction(transaction_id, user_id, **kwargs):
    allowed = ['title', 'amount', 'type', 'category', 'date', 'notes']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    p = ph()
    set_clause = ', '.join([f"{k} = {p}" for k in updates.keys()])
    values = list(updates.values()) + [transaction_id, user_id]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE transactions SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = {p} AND user_id = {p}',
            values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_transaction(transaction_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM transactions WHERE id = {ph()} AND user_id = {ph()}',
            (transaction_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_transaction_summary(user_id, month=None, year=None):
    p = ph()
    if DB_TYPE == 'mysql':
        date_filter = f' AND MONTH(date) = {p} AND YEAR(date) = {p}'
    elif DB_TYPE == 'postgresql':
        date_filter = f' AND EXTRACT(MONTH FROM date) = {p} AND EXTRACT(YEAR FROM date) = {p}'
    else:
        date_filter = f' AND strftime("%m", date) = {p} AND strftime("%Y", date) = {p}'

    query  = f'SELECT type, SUM(amount) as total, COUNT(*) as count FROM transactions WHERE user_id = {p}'
    params = [user_id]

    if month and year:
        query += date_filter
        if DB_TYPE == 'sqlite':
            params.extend([f'{month:02d}', str(year)])
        else:
            params.extend([month, year])

    query += ' GROUP BY type'

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def get_category_breakdown(user_id, trans_type='expense', month=None, year=None):
    p = ph()
    if DB_TYPE == 'mysql':
        date_filter = f' AND MONTH(date) = {p} AND YEAR(date) = {p}'
    elif DB_TYPE == 'postgresql':
        date_filter = f' AND EXTRACT(MONTH FROM date) = {p} AND EXTRACT(YEAR FROM date) = {p}'
    else:
        date_filter = f' AND strftime("%m", date) = {p} AND strftime("%Y", date) = {p}'

    query  = f'SELECT category, SUM(amount) as total, COUNT(*) as count FROM transactions WHERE user_id = {p} AND type = {p}'
    params = [user_id, trans_type]

    if month and year:
        query += date_filter
        if DB_TYPE == 'sqlite':
            params.extend([f'{month:02d}', str(year)])
        else:
            params.extend([month, year])

    query += ' GROUP BY category ORDER BY total DESC'

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


# ==================== BUDGET OPERATIONS ====================

def create_budget(user_id, category, amount, alert_threshold=80):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f'INSERT INTO budgets (user_id, category, amount, alert_threshold) VALUES ({placeholders(4)})',
                (user_id, category, amount, alert_threshold)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception:
            return None


def get_budgets(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM budgets WHERE user_id = {ph()}', (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def update_budget(budget_id, user_id, **kwargs):
    allowed = ['amount', 'alert_threshold']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    p = ph()
    set_clause = ', '.join([f"{k} = {p}" for k in updates.keys()])
    values = list(updates.values()) + [budget_id, user_id]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE budgets SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = {p} AND user_id = {p}',
            values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_budget(budget_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM budgets WHERE id = {ph()} AND user_id = {ph()}',
            (budget_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ==================== DASHBOARD ====================

def get_dashboard_data(user_id):
    now = datetime.now()
    p   = ph()

    with get_db() as conn:
        cursor = conn.cursor()

        # Total balance
        cursor.execute(f'''
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income'  THEN amount ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as balance
            FROM transactions WHERE user_id = {p}
        ''', (user_id,))
        result  = cursor.fetchone()
        balance = dict(result)['balance'] if result else 0

        # Month income / expense
        if DB_TYPE == 'mysql':
            cursor.execute(f'''
                SELECT
                    COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) as income,
                    COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) as expense
                FROM transactions
                WHERE user_id={p} AND MONTH(date)={p} AND YEAR(date)={p}
            ''', (user_id, now.month, now.year))
        elif DB_TYPE == 'postgresql':
            cursor.execute(f'''
                SELECT
                    COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) as income,
                    COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) as expense
                FROM transactions
                WHERE user_id={p} AND EXTRACT(MONTH FROM date)={p} AND EXTRACT(YEAR FROM date)={p}
            ''', (user_id, now.month, now.year))
        else:
            cursor.execute(f'''
                SELECT
                    COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) as income,
                    COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) as expense
                FROM transactions
                WHERE user_id={p}
                  AND strftime("%m", date) = {p}
                  AND strftime("%Y", date) = {p}
            ''', (user_id, f'{now.month:02d}', str(now.year)))

        month_data = dict(cursor.fetchone())
        income  = month_data.get('income', 0)
        expense = month_data.get('expense', 0)

        # Recent transactions
        cursor.execute(f'''
            SELECT * FROM transactions WHERE user_id = {p}
            ORDER BY date DESC, created_at DESC LIMIT 5
        ''', (user_id,))
        recent = [dict(r) for r in cursor.fetchall()]

        return {
            'balance':            float(balance) if balance else 0,
            'monthIncome':        float(income)  if income  else 0,
            'monthExpense':       float(expense) if expense else 0,
            'recentTransactions': recent
        }


# ==================== RECURRING ====================

def create_recurring(user_id, title, amount, trans_type, frequency, category,
                     start_date, end_date=None, notes=''):
    new_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO recurring
                (id, user_id, title, amount, type, frequency, category,
                 start_date, end_date, notes, is_active)
            VALUES ({placeholders(11)})
        ''', (new_id, user_id, title, amount, trans_type, frequency,
              category, start_date, end_date or None, notes, 1))
        conn.commit()
        return new_id


def get_recurring(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM recurring WHERE user_id = {ph()} ORDER BY is_active DESC, title ASC',
            (user_id,)
        )
        rows = []
        for r in cursor.fetchall():
            row = dict(r)
            for field in ('start_date', 'end_date', 'last_posted'):
                if row.get(field) is not None:
                    row[field] = str(row[field])[:10]
                else:
                    row[field] = None
            rows.append(row)
        return rows

def update_recurring(item_id, user_id, **kwargs):
    allowed = ['title', 'amount', 'type', 'frequency', 'category',
               'start_date', 'end_date', 'notes', 'is_active', 'last_posted']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    p = ph()
    set_clause = ', '.join([f"{k} = {p}" for k in updates.keys()])
    values = list(updates.values()) + [item_id, user_id]
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE recurring SET {set_clause} WHERE id = {p} AND user_id = {p}',
            values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_recurring(item_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM recurring WHERE id = {ph()} AND user_id = {ph()}',
            (item_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ==================== GOALS ====================

def create_goal(user_id, title, target_amount, target_date, current_amount=0, notes=''):
    new_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            INSERT INTO goals (id, user_id, title, target_amount, current_amount, target_date, notes)
            VALUES ({placeholders(7)})
        ''', (new_id, user_id, title, target_amount, current_amount, target_date, notes))
        conn.commit()
        return new_id


def get_goals(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM goals WHERE user_id = {ph()} ORDER BY target_date DESC',
            (user_id,)
        )
        return [dict(r) for r in cursor.fetchall()]


def delete_goal(goal_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM goals WHERE id = {ph()} AND user_id = {ph()}',
            (goal_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ==================== ASSETS ====================

def create_asset(user_id, name, value):
    new_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'INSERT INTO assets (id, user_id, name, value) VALUES ({placeholders(4)})',
            (new_id, user_id, name, value)
        )
        conn.commit()
        return new_id


def get_assets(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM assets WHERE user_id = {ph()}', (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def delete_asset(item_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM assets WHERE id = {ph()} AND user_id = {ph()}',
            (item_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ==================== LIABILITIES ====================

def create_liability(user_id, name, amount):
    new_id = str(uuid.uuid4())
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'INSERT INTO liabilities (id, user_id, name, amount) VALUES ({placeholders(4)})',
            (new_id, user_id, name, amount)
        )
        conn.commit()
        return new_id


def get_liabilities(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM liabilities WHERE user_id = {ph()}', (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def delete_liability(item_id, user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM liabilities WHERE id = {ph()} AND user_id = {ph()}',
            (item_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# ==================== ADMIN STATS ====================

def get_admin_stats():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = dict(cursor.fetchone())['count']

        cursor.execute(f"SELECT COUNT(*) as count FROM users WHERE status = {ph()}", ('active',))
        active_users = dict(cursor.fetchone())['count']

        cursor.execute('SELECT COUNT(*) as count FROM transactions')
        total_transactions = dict(cursor.fetchone())['count']

        cursor.execute("""
            SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END),0) as total
            FROM transactions
        """)
        total_revenue = dict(cursor.fetchone())['total']

        cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
        admin_count = dict(cursor.fetchone())['count']

        return {
            'totalUsers':        total_users,
            'activeUsers':       active_users,
            'totalTransactions': total_transactions,
            'totalRevenue':      float(total_revenue) if total_revenue else 0,
            'activePercentage':  round((active_users / total_users * 100) if total_users > 0 else 0, 1),
            'adminCount':        admin_count
        }


# ==================== STARTUP ====================

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("TRAKN Database Initialization")
    print("=" * 50 + "\n")
    init_db()
    create_default_admin()
    print("\n" + "=" * 50)