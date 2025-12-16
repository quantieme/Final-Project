"""
Database Setup Module
Creates and manages SQLite database for cryptocurrency and stock analysis
"""

import sqlite3
import os
from config import DATABASE_NAME, CRYPTO_SYMBOLS

DB_NAME = DATABASE_NAME


def date_string_to_int(date_string):
    """
    Convert date string to integer to avoid duplicate strings

    Args:
        date_string: Date in format 'YYYY-MM-DD' (e.g., '2025-12-15')

    Returns:
        int: Date as integer (e.g., 20251215)

    Example:
        '2025-12-15' -> 20251215
        '2024-01-05' -> 20240105
    """
    # Remove dashes and convert to integer
    return int(date_string.replace('-', ''))


def date_int_to_string(date_int):
    """
    Convert integer date back to string format for display

    Args:
        date_int: Date as integer (e.g., 20251215)

    Returns:
        str: Date in format 'YYYY-MM-DD' (e.g., '2025-12-15')

    Example:
        20251215 -> '2025-12-15'
        20240105 -> '2024-01-05'
    """
    date_str = str(date_int)
    return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"


def get_db_connection():
    """
    Create and return a database connection

    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def create_tables():
    """
    Create all required database tables if they don't exist

    Tables created:
    - crypto_symbol: Lookup table for cryptocurrency symbols (with integer ID)
    - crypto_price: Historical cryptocurrency price data
    - stock_price: Historical stock price data
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Table 1: crypto_symbol (lookup table with integer key)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_symbol (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """)

    # Table 2: crypto_price (shares integer key with crypto_symbol)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crypto_price (
            date INTEGER NOT NULL,
            crypto_id INTEGER NOT NULL,
            price_usd REAL NOT NULL,
            market_cap REAL,
            volume REAL,
            PRIMARY KEY (date, crypto_id),
            FOREIGN KEY (crypto_id) REFERENCES crypto_symbol(id)
        )
    """)

    # Table 3: stock_symbol (lookup table with integer key)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_symbol (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    """)

    # Table 4: stock_price (shares integer key with stock_symbol)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_price (
            date INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            PRIMARY KEY (date, stock_id),
            FOREIGN KEY (stock_id) REFERENCES stock_symbol(id)
        )
    """)

    conn.commit()
    conn.close()
    print("Database tables created successfully!")


def insert_crypto_symbol(symbol, name):
    """
    Insert a cryptocurrency symbol into the lookup table
    Returns the crypto_id (integer key)

    Args:
        symbol: Crypto ticker (e.g., 'BTC')
        name: Full name (e.g., 'Bitcoin')

    Returns:
        int: The crypto_id for this symbol
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if symbol already exists
    cur.execute("SELECT id FROM crypto_symbol WHERE symbol = ?", (symbol,))
    result = cur.fetchone()

    if result:
        crypto_id = result['id']
    else:
        # Insert new symbol
        cur.execute("""
            INSERT INTO crypto_symbol (symbol, name)
            VALUES (?, ?)
        """, (symbol, name))
        conn.commit()
        crypto_id = cur.lastrowid

    conn.close()
    return crypto_id


def get_crypto_id(symbol):
    """
    Get the integer ID for a crypto symbol

    Args:
        symbol: Crypto ticker (e.g., 'BTC')

    Returns:
        int: The crypto_id, or None if not found
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM crypto_symbol WHERE symbol = ?", (symbol,))
    result = cur.fetchone()

    conn.close()

    if result:
        return result['id']
    return None


def get_last_crypto_date(crypto_id):
    """
    Get the most recent date for a specific cryptocurrency

    Args:
        crypto_id: Integer ID of the cryptocurrency

    Returns:
        str: Most recent date, or None if no data exists
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(date) as last_date
        FROM crypto_price
        WHERE crypto_id = ?
    """, (crypto_id,))

    result = cur.fetchone()
    conn.close()

    return result['last_date'] if result['last_date'] else None


def insert_stock_symbol(symbol, name):
    """
    Insert a stock symbol into the lookup table
    Returns the stock_id (integer key)

    Args:
        symbol: Stock ticker (e.g., 'NVDA')
        name: Company name (e.g., 'NVIDIA Corporation')

    Returns:
        int: The stock_id for this symbol
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if symbol already exists
    cur.execute("SELECT id FROM stock_symbol WHERE symbol = ?", (symbol,))
    result = cur.fetchone()

    if result:
        stock_id = result['id']
    else:
        # Insert new symbol
        cur.execute("""
            INSERT INTO stock_symbol (symbol, name)
            VALUES (?, ?)
        """, (symbol, name))
        conn.commit()
        stock_id = cur.lastrowid

    conn.close()
    return stock_id


def get_stock_id(symbol):
    """
    Get the integer ID for a stock symbol

    Args:
        symbol: Stock ticker (e.g., 'NVDA')

    Returns:
        int: The stock_id, or None if not found
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM stock_symbol WHERE symbol = ?", (symbol,))
    result = cur.fetchone()

    conn.close()

    if result:
        return result['id']
    return None


def get_last_stock_date(stock_id):
    """
    Get the most recent date for a specific stock

    Args:
        stock_id: Integer ID of the stock

    Returns:
        str: Most recent date, or None if no data exists
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT MAX(date) as last_date
        FROM stock_price
        WHERE stock_id = ?
    """, (stock_id,))

    result = cur.fetchone()
    conn.close()

    return result['last_date'] if result['last_date'] else None


def get_crypto_row_count(crypto_id):
    """
    Count how many rows exist for a specific cryptocurrency

    Args:
        crypto_id: Integer ID of the cryptocurrency

    Returns:
        int: Number of rows
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) as count
        FROM crypto_price
        WHERE crypto_id = ?
    """, (crypto_id,))

    result = cur.fetchone()
    conn.close()

    return result['count']


def get_stock_row_count(stock_id):
    """
    Count how many rows exist for a specific stock

    Args:
        stock_id: Integer ID of the stock

    Returns:
        int: Number of rows
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) as count
        FROM stock_price
        WHERE stock_id = ?
    """, (stock_id,))

    result = cur.fetchone()
    conn.close()

    return result['count']


def check_crypto_data_exists(crypto_id, date):
    """
    Check if data already exists for a specific crypto and date

    Args:
        crypto_id: Integer ID of the cryptocurrency
        date: Date string (YYYY-MM-DD)

    Returns:
        bool: True if data exists, False otherwise
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM crypto_price
        WHERE crypto_id = ? AND date = ?
    """, (crypto_id, date))

    result = cur.fetchone()
    conn.close()

    return result is not None


def check_stock_data_exists(stock_id, date):
    """
    Check if data already exists for a specific stock and date

    Args:
        stock_id: Integer ID of the stock
        date: Date string (YYYY-MM-DD)

    Returns:
        bool: True if data exists, False otherwise
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM stock_price
        WHERE stock_id = ? AND date = ?
    """, (stock_id, date))

    result = cur.fetchone()
    conn.close()

    return result is not None


def initialize_database():
    """
    Initialize the database with tables and both crypto and stock symbols
    Call this once at the start of the project
    """
    create_tables()

    # Insert cryptocurrency symbols (creates integer keys)
    print("Initializing cryptocurrency symbols...")
    for symbol, info in CRYPTO_SYMBOLS.items():
        name = info['name']
        crypto_id = insert_crypto_symbol(symbol, name)
        print(f"  {name} ({symbol}) with ID: {crypto_id}")

    # Insert stock symbols (creates integer keys)
    print("\nInitializing stock symbols...")
    stock_configs = {
        'NVDA': 'NVIDIA Corporation',
        'AMD': 'Advanced Micro Devices',
        'COIN': 'Coinbase Global Inc'
    }
    for symbol, name in stock_configs.items():
        stock_id = insert_stock_symbol(symbol, name)
        print(f"  {name} ({symbol}) with ID: {stock_id}")


if __name__ == "__main__":
    # Run this file directly to initialize the database
    initialize_database()
    print("\nDatabase initialization complete!")
    print(f"Database file: {DB_NAME}")
