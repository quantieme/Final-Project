"""
Stock Data Collection Module
Fetches historical stock data from Alpha Vantage API
Stores data in database with 25-row limit per run
"""

import requests
import time
from database_setup import (
    get_db_connection,
    get_stock_id,
    get_last_stock_date,
    get_stock_row_count,
    check_stock_data_exists,
    create_tables,
    date_string_to_int
)
from config import (
    ALPHA_VANTAGE_API_KEY,
    ALPHA_VANTAGE_BASE_URL,
    STOCK_SYMBOLS,
    MAX_ROWS_PER_RUN
)

# Alpha Vantage API Configuration (from config file)
API_KEY = ALPHA_VANTAGE_API_KEY
BASE_URL = ALPHA_VANTAGE_BASE_URL


def fetch_stock_history(symbol):
    """
    Fetch historical daily stock data from Alpha Vantage API

    Args:
        symbol: Stock ticker (e.g., 'NVDA')

    Returns:
        dict: JSON response with time series data
              Returns None if request fails
    """
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': API_KEY,
        'outputsize': 'compact'  # Get last 100 days (full is premium-only)
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Check for API errors
        if 'Error Message' in data:
            print(f"API Error for {symbol}: {data['Error Message']}")
            return None

        if 'Note' in data:
            print(f"API Rate Limit Note: {data['Note']}")
            return None

        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def parse_stock_data(data, symbol):
    """
    Parse Alpha Vantage API response into list of daily records

    Args:
        data: JSON response from Alpha Vantage
        symbol: Stock ticker

    Returns:
        list: List of tuples (date, stock_id, open, high, low, close, volume)
    """
    if not data or 'Time Series (Daily)' not in data:
        return []

    # Get the integer stock_id for this symbol
    stock_id = get_stock_id(symbol)
    if stock_id is None:
        print(f"Error: Stock symbol {symbol} not found in database")
        return []

    time_series = data['Time Series (Daily)']
    records = []

    for date_string, values in time_series.items():
        try:
            # Convert date string to integer to avoid duplicate strings
            date_int = date_string_to_int(date_string)

            open_price = float(values['1. open'])
            high_price = float(values['2. high'])
            low_price = float(values['3. low'])
            close_price = float(values['4. close'])
            volume = int(values['5. volume'])

            records.append((date_int, stock_id, open_price, high_price, low_price, close_price, volume))
        except (KeyError, ValueError) as e:
            print(f"Error parsing data for {symbol} on {date_string}: {e}")
            continue

    return records


def insert_stock_data(records, symbol, max_rows=MAX_ROWS_PER_RUN):
    """
    Insert stock records into database
    Limits to max_rows and avoids duplicates

    Args:
        records: List of tuples (date, stock_id, open, high, low, close, volume)
        symbol: Stock ticker for logging
        max_rows: Maximum number of rows to insert

    Returns:
        int: Number of rows actually inserted
    """
    conn = get_db_connection()
    cur = conn.cursor()

    inserted_count = 0
    skipped_count = 0

    for record in records:
        date, stock_id, open_price, high_price, low_price, close_price, volume = record

        # Check if already exists (avoid duplicates)
        if check_stock_data_exists(stock_id, date):
            skipped_count += 1
            continue

        # Check if we've reached the limit for this run
        if inserted_count >= max_rows:
            print(f"Reached limit of {max_rows} rows for this run")
            break

        try:
            cur.execute("""
                INSERT INTO stock_price (date, stock_id, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, stock_id, open_price, high_price, low_price, close_price, volume))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting data for {symbol} on {date}: {e}")

    conn.commit()
    conn.close()

    print(f"{symbol}: Inserted {inserted_count} rows, Skipped {skipped_count} duplicates")
    return inserted_count


def collect_stock_data():
    """
    Main function to collect stock data
    Fetches data for all configured stock symbols
    Respects 25-row limit per run across all stocks
    """
    print("=" * 60)
    print("Starting Stock Data Collection")
    print(f"Using API Key: {API_KEY[:8]}...")
    print("=" * 60)

    total_inserted = 0

    for symbol in STOCK_SYMBOLS:
        stock_id = get_stock_id(symbol)
        if stock_id is None:
            print(f"\nWarning: {symbol} not found in database. Run database_setup.py first.")
            continue

        # Check how many rows we already have
        existing_rows = get_stock_row_count(stock_id)
        print(f"\n{symbol}:")
        print(f"  Existing rows in database: {existing_rows}")

        # Check remaining quota for this run
        remaining_quota = MAX_ROWS_PER_RUN - total_inserted
        if remaining_quota <= 0:
            print(f"  Skipping - already inserted {MAX_ROWS_PER_RUN} rows this run")
            continue

        # Fetch data from API
        print(f"  Fetching data from Alpha Vantage API...")
        data = fetch_stock_history(symbol)

        if data is None:
            print(f"  Failed to fetch data for {symbol}")
            continue

        # Parse the data
        records = parse_stock_data(data, symbol)
        print(f"  Retrieved {len(records)} records from API")

        if not records:
            print(f"  No records to process")
            continue

        # Sort by date to insert oldest first
        records.sort(key=lambda x: x[0])

        # Insert into database (pass all records, function will handle limit and duplicates)
        inserted = insert_stock_data(records, symbol, remaining_quota)
        total_inserted += inserted

        # IMPORTANT: Alpha Vantage free tier has rate limits
        # Wait 12 seconds between requests (5 calls per minute limit)
        if symbol != STOCK_SYMBOLS[-1]:  # Don't wait after last symbol
            print("  Waiting 12 seconds (API rate limit)...")
            time.sleep(12)

        # Stop if we've reached the limit
        if total_inserted >= MAX_ROWS_PER_RUN:
            print(f"\nReached total limit of {MAX_ROWS_PER_RUN} rows for this run")
            break

    print("\n" + "=" * 60)
    print(f"Data collection complete! Total rows inserted: {total_inserted}")
    print("=" * 60)

    # Show summary
    print("\nCurrent database status:")
    for symbol in STOCK_SYMBOLS:
        stock_id = get_stock_id(symbol)
        if stock_id:
            count = get_stock_row_count(stock_id)
            print(f"  {symbol}: {count} total rows")


if __name__ == "__main__":
    # Make sure database tables exist
    try:
        create_tables()
    except Exception as e:
        print(f"Error creating tables: {e}")

    # Collect stock data
    collect_stock_data()

    print("\n" + "=" * 60)
    print("To gather more data, run this script again!")
    print("Each run will insert up to 25 new rows.")
    print("\nNOTE: Alpha Vantage free tier limits:")
    print("  - 25 API calls per day")
    print("  - 5 API calls per minute")
    print("=" * 60)
