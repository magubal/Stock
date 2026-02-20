"""
Data Models and Database Initialization
"""
import sqlite3


def init_db(db_path):
    """Initialize SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Stock Prices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    
    # Stock Info Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_info (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            currency TEXT,
            market TEXT,
            last_updated TEXT
        )
    ''')
    
    # Research Notes Table (for Research skill)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            category TEXT,
            title TEXT,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Decision Scenarios Table (for Decision skill)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decision_scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            scenario_type TEXT,
            condition TEXT,
            action TEXT,
            target_price REAL,
            stop_loss REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[OK] Database initialized: {db_path}")


def get_db_connection(db_path):
    """Get database connection"""
    return sqlite3.connect(db_path)
