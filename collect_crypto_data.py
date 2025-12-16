"""
Cryptocurrency Data Collection Module
Fetches historical price data from CoinGecko API
Stores data in database with 25-row limit per run
"""

import requests
import time
from datetime import datetime, timedelta
from database_setup import (
    get_db_connection,
    get_crypto_id,
    get_last_crypto_date,
    get_crypto_row_count,
    check_crypto_data_exists,
    initialize_database,
    date_string_to_int
)
from config import COINGECKO_BASE_URL, CRYPTO_SYMBOLS, MAX_ROWS_PER_RUN

# CoinGecko API endpoint (no key required)
BASE_URL = COINGECKO_BASE_URL

# Cryptocurrency configurations (from config)
CRYPTO_CONFIGS = {symbol: info['coingecko_id'] for symbol, info in CRYPTO_SYMBOLS.items()}


def fetch_crypto_history(coin_id, days=90):
    """
    Fetch historical price data from CoinGecko API

    Args:
        coin_id: CoinGecko coin identifier (e.g., 'bitcoin')
        days: Number of days of history to fetch

    Returns:
        dict: JSON response with prices, market_caps, and volumes
              Returns None if request fails
    """
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {coin_id}: {e}")
        return None


def parse_crypto_data(data, crypto_symbol):
    """
    Parse CoinGecko API response into list of daily records

    Args:
        data: JSON response from CoinGecko
        crypto_symbol: Crypto ticker (e.g., 'BTC')

    Returns:
        list: List of tuples (date, crypto_id, price, market_cap, volume)
    """
    if not data or 'prices' not in data:
        return []

    crypto_id = get_crypto_id(crypto_symbol)
    if crypto_id is None:
        print(f"Error: Crypto symbol {crypto_symbol} not found in database")
        return []

    records = []
    prices = data['prices']
    market_caps = data.get('market_caps', [])
    volumes = data.get('total_volumes', [])

    # Ensure all lists have same length
    min_length = min(len(prices), len(market_caps), len(volumes))

    for i in range(min_length):
        # Convert timestamp to date string
        timestamp_ms = prices[i][0]
        date_string = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')

        # Convert date string to integer to avoid duplicate strings
        date_int = date_string_to_int(date_string)

        price = prices[i][1]
        market_cap = market_caps[i][1] if i < len(market_caps) else None
        volume = volumes[i][1] if i < len(volumes) else None

        records.append((date_int, crypto_id, price, market_cap, volume))

    return records


def insert_crypto_data(records, crypto_symbol, max_rows=MAX_ROWS_PER_RUN):
    """
    Insert cryptocurrency records into database
    Limits to max_rows and avoids duplicates

    Args:
        records: List of tuples (date, crypto_id, price, market_cap, volume)
        crypto_symbol: Crypto ticker for logging
        max_rows: Maximum number of rows to insert

    Returns:
        int: Number of rows actually inserted
    """
    conn = get_db_connection()
    cur = conn.cursor()

    inserted_count = 0
    skipped_count = 0

    for record in records:
        date, crypto_id, price, market_cap, volume = record

        # Check if already exists (avoid duplicates)
        if check_crypto_data_exists(crypto_id, date):
            skipped_count += 1
            continue

        # Check if we've reached the limit for this run
        if inserted_count >= max_rows:
            print(f"Reached limit of {MAX_ROWS_PER_RUN} rows for this run")
            break

        try:
            cur.execute("""
                INSERT INTO crypto_price (date, crypto_id, price_usd, market_cap, volume)
                VALUES (?, ?, ?, ?, ?)
            """, (date, crypto_id, price, market_cap, volume))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting data for {crypto_symbol} on {date}: {e}")

    conn.commit()
    conn.close()

    print(f"{crypto_symbol}: Inserted {inserted_count} rows, Skipped {skipped_count} duplicates")
    return inserted_count


def collect_crypto_data():
    """
    Main function to collect cryptocurrency data
    Fetches data for all configured cryptocurrencies
    Respects 25-row limit per run across all cryptos
    """
    print("=" * 60)
    print("Starting Cryptocurrency Data Collection")
    print("=" * 60)

    total_inserted = 0

    for symbol, coin_id in CRYPTO_CONFIGS.items():
        crypto_id = get_crypto_id(symbol)
        if crypto_id is None:
            print(f"Warning: {symbol} not found in database. Run database_setup.py first.")
            continue

        # Check how many rows we already have
        existing_rows = get_crypto_row_count(crypto_id)
        print(f"\n{symbol} ({coin_id}):")
        print(f"  Existing rows in database: {existing_rows}")

        # Check remaining quota for this run
        remaining_quota = MAX_ROWS_PER_RUN - total_inserted
        if remaining_quota <= 0:
            print(f"  Skipping - already inserted {MAX_ROWS_PER_RUN} rows this run")
            continue

        # Fetch data from API
        print(f"  Fetching data from CoinGecko API...")
        data = fetch_crypto_history(coin_id, days=180)

        if data is None:
            print(f"  Failed to fetch data for {symbol}")
            continue

        # Parse the data
        records = parse_crypto_data(data, symbol)
        print(f"  Retrieved {len(records)} records from API")

        if not records:
            print(f"  No records to process")
            continue

        # Sort by date to insert oldest first
        records.sort(key=lambda x: x[0])

        # Insert into database (pass all records, function will handle limit and duplicates)
        inserted = insert_crypto_data(records, symbol, remaining_quota)
        total_inserted += inserted

        # Rate limiting - be nice to the API
        time.sleep(1.5)

        # Stop if we've reached the limit
        if total_inserted >= MAX_ROWS_PER_RUN:
            print(f"\nReached total limit of {MAX_ROWS_PER_RUN} rows for this run")
            break

    print("\n" + "=" * 60)
    print(f"Data collection complete! Total rows inserted: {total_inserted}")
    print("=" * 60)

    # Show summary
    print("\nCurrent database status:")
    for symbol in CRYPTO_CONFIGS.keys():
        crypto_id = get_crypto_id(symbol)
        if crypto_id:
            count = get_crypto_row_count(crypto_id)
            print(f"  {symbol}: {count} total rows")


if __name__ == "__main__":
    # Make sure database is initialized
    try:
        # Test if tables exist by trying to get a crypto_id
        test_id = get_crypto_id('BTC')
        if test_id is None:
            print("Database not initialized. Initializing now...")
            initialize_database()
    except Exception:
        print("Database not initialized. Initializing now...")
        initialize_database()

    # Collect crypto data
    collect_crypto_data()

    print("\n" + "=" * 60)
    print("To gather more data, run this script again!")
    print("Each run will insert up to 25 new rows.")
    print("=" * 60)
