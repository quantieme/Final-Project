"""
Data Analysis and Calculation Module
Performs calculations on stored data using SQL queries with JOINs
Writes results to output file
"""

from database_setup import get_db_connection, date_int_to_string
from config import OUTPUT_DIR, RESULTS_FILE
import math
import os


def get_crypto_prices_with_symbols():
    """
    Retrieve all crypto price data with symbol names using JOIN

    Returns:
        list: List of dict rows with date, symbol, name, price, volume
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # SQL JOIN to combine crypto_price with crypto_symbol
    query = """
        SELECT
            cp.date,
            cs.symbol,
            cs.name,
            cp.price_usd,
            cp.market_cap,
            cp.volume
        FROM crypto_price cp
        JOIN crypto_symbol cs ON cp.crypto_id = cs.id
        ORDER BY cs.symbol, cp.date
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_stock_prices_with_symbols():
    """
    Retrieve all stock price data with symbol names using JOIN

    Returns:
        list: List of dict rows with date, symbol, name, open, high, low, close, volume
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # SQL JOIN to combine stock_price with stock_symbol
    query = """
        SELECT
            sp.date,
            ss.symbol,
            ss.name,
            sp.open,
            sp.high,
            sp.low,
            sp.close,
            sp.volume
        FROM stock_price sp
        JOIN stock_symbol ss ON sp.stock_id = ss.id
        ORDER BY ss.symbol, sp.date
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def calculate_crypto_volatility(crypto_data):
    """
    Calculate daily volatility for cryptocurrencies
    Volatility = price range as percentage of price

    Args:
        crypto_data: List of crypto price records

    Returns:
        dict: {symbol: [(date, volatility), ...]}
    """
    # Group by symbol
    by_symbol = {}
    for row in crypto_data:
        symbol = row['symbol']
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(row)

    volatility_data = {}

    for symbol, prices in by_symbol.items():
        volatilities = []

        for i in range(1, len(prices)):
            # For crypto, estimate high/low from price variations
            # Use 2% range as estimate (crypto typically has intraday volatility)
            current_price = prices[i]['price_usd']
            prev_price = prices[i-1]['price_usd']

            # Estimate volatility from price change
            price_change = abs(current_price - prev_price)
            volatility = (price_change / prev_price) * 100 if prev_price > 0 else 0

            volatilities.append((prices[i]['date'], volatility))

        volatility_data[symbol] = volatilities

    return volatility_data


def calculate_stock_volatility(stock_data):
    """
    Calculate daily volatility for stocks
    Volatility = (high - low) / close * 100

    Args:
        stock_data: List of stock price records

    Returns:
        dict: {symbol: [(date, volatility), ...]}
    """
    # Group by symbol
    by_symbol = {}
    for row in stock_data:
        symbol = row['symbol']
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(row)

    volatility_data = {}

    for symbol, prices in by_symbol.items():
        volatilities = []

        for price in prices:
            high = price['high']
            low = price['low']
            close = price['close']

            volatility = ((high - low) / close * 100) if close > 0 else 0
            volatilities.append((price['date'], volatility))

        volatility_data[symbol] = volatilities

    return volatility_data


def calculate_price_momentum(data, symbol_key='symbol', price_key='price_usd', window=7):
    """
    Calculate price momentum over a time window
    Momentum = (price_today - price_N_days_ago) / price_N_days_ago * 100

    Args:
        data: List of price records
        symbol_key: Key name for symbol in data
        price_key: Key name for price in data
        window: Number of days to look back

    Returns:
        dict: {symbol: [(date, momentum), ...]}
    """
    # Group by symbol
    by_symbol = {}
    for row in data:
        symbol = row[symbol_key]
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(row)

    momentum_data = {}

    for symbol, prices in by_symbol.items():
        momentums = []

        for i in range(window, len(prices)):
            current_price = prices[i][price_key]
            past_price = prices[i - window][price_key]

            if past_price > 0:
                momentum = ((current_price - past_price) / past_price) * 100
            else:
                momentum = 0

            momentums.append((prices[i]['date'], momentum))

        momentum_data[symbol] = momentums

    return momentum_data


def calculate_daily_returns(data, symbol_key='symbol', price_key='price_usd'):
    """
    Calculate daily percentage returns

    Args:
        data: List of price records
        symbol_key: Key for symbol
        price_key: Key for price

    Returns:
        dict: {symbol: [(date, return_pct), ...]}
    """
    by_symbol = {}
    for row in data:
        symbol = row[symbol_key]
        if symbol not in by_symbol:
            by_symbol[symbol] = []
        by_symbol[symbol].append(row)

    returns_data = {}

    for symbol, prices in by_symbol.items():
        returns = []

        for i in range(1, len(prices)):
            current_price = prices[i][price_key]
            prev_price = prices[i-1][price_key]

            if prev_price > 0:
                daily_return = ((current_price - prev_price) / prev_price) * 100
            else:
                daily_return = 0

            returns.append((prices[i]['date'], daily_return))

        returns_data[symbol] = returns

    return returns_data


def calculate_correlation(series1, series2):
    """
    Calculate Pearson correlation coefficient between two series

    Args:
        series1: List of (date, value) tuples
        series2: List of (date, value) tuples

    Returns:
        float: Correlation coefficient (-1 to 1), or 0 if can't calculate
    """
    # Create dictionaries for easy matching by date
    dict1 = {date: value for date, value in series1}
    dict2 = {date: value for date, value in series2}

    # Find common dates
    common_dates = sorted(set(dict1.keys()) & set(dict2.keys()))

    if len(common_dates) < 2:
        return 0.0

    # Get aligned values
    values1 = [dict1[date] for date in common_dates]
    values2 = [dict2[date] for date in common_dates]

    # Calculate means
    mean1 = sum(values1) / len(values1)
    mean2 = sum(values2) / len(values2)

    # Calculate correlation
    numerator = sum((v1 - mean1) * (v2 - mean2) for v1, v2 in zip(values1, values2))

    sum_sq1 = sum((v1 - mean1) ** 2 for v1 in values1)
    sum_sq2 = sum((v2 - mean2) ** 2 for v2 in values2)

    denominator = math.sqrt(sum_sq1 * sum_sq2)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_average_volatility(volatility_data):
    """
    Calculate average volatility for each symbol

    Args:
        volatility_data: Dict of {symbol: [(date, volatility), ...]}

    Returns:
        dict: {symbol: avg_volatility}
    """
    averages = {}
    for symbol, data in volatility_data.items():
        if data:
            avg = sum(vol for _, vol in data) / len(data)
            averages[symbol] = avg
        else:
            averages[symbol] = 0.0
    return averages


def find_top_momentum_days(momentum_data, top_n=5):
    """
    Find days with highest absolute momentum for each symbol

    Args:
        momentum_data: Dict of {symbol: [(date, momentum), ...]}
        top_n: Number of top days to return

    Returns:
        dict: {symbol: [(date, momentum), ...]}
    """
    top_days = {}
    for symbol, data in momentum_data.items():
        # Sort by absolute momentum value
        sorted_data = sorted(data, key=lambda x: abs(x[1]), reverse=True)
        top_days[symbol] = sorted_data[:top_n]
    return top_days


def perform_analysis():
    """
    Main analysis function
    Performs all calculations and returns results
    """
    print("=" * 60)
    print("Performing Data Analysis")
    print("=" * 60)

    # Fetch data from database using JOIN
    print("\nFetching data from database (using JOIN)...")
    crypto_data = get_crypto_prices_with_symbols()
    stock_data = get_stock_prices_with_symbols()

    print(f"Loaded {len(crypto_data)} crypto price records")
    print(f"Loaded {len(stock_data)} stock price records")

    if not crypto_data or not stock_data:
        print("\nError: Not enough data in database!")
        print("Run collect_crypto_data.py and collect_stock_data.py first.")
        return None

    # Calculate volatilities
    print("\nCalculating volatilities...")
    crypto_volatility = calculate_crypto_volatility(crypto_data)
    stock_volatility = calculate_stock_volatility(stock_data)

    # Calculate momentum
    print("Calculating 7-day momentum...")
    crypto_momentum = calculate_price_momentum(crypto_data, 'symbol', 'price_usd', 7)
    stock_momentum = calculate_price_momentum(stock_data, 'symbol', 'close', 7)

    # Calculate daily returns
    print("Calculating daily returns...")
    crypto_returns = calculate_daily_returns(crypto_data, 'symbol', 'price_usd')
    stock_returns = calculate_daily_returns(stock_data, 'symbol', 'close')

    # Calculate correlations between cryptos and stocks
    print("Calculating cross-market correlations...")
    correlations = {}

    for crypto_symbol, crypto_ret in crypto_returns.items():
        for stock_symbol, stock_ret in stock_returns.items():
            pair = f"{crypto_symbol}-{stock_symbol}"
            corr = calculate_correlation(crypto_ret, stock_ret)
            correlations[pair] = corr

    # Calculate average volatilities
    avg_crypto_vol = calculate_average_volatility(crypto_volatility)
    avg_stock_vol = calculate_average_volatility(stock_volatility)

    # Find top momentum days
    top_crypto_momentum = find_top_momentum_days(crypto_momentum, 5)
    top_stock_momentum = find_top_momentum_days(stock_momentum, 5)

    results = {
        'correlations': correlations,
        'avg_crypto_volatility': avg_crypto_vol,
        'avg_stock_volatility': avg_stock_vol,
        'top_crypto_momentum': top_crypto_momentum,
        'top_stock_momentum': top_stock_momentum,
        'crypto_returns': crypto_returns,
        'stock_returns': stock_returns
    }

    print("\nAnalysis complete!")
    return results


def write_results_to_file(results, filename=None):
    """
    Write analysis results to a text file

    Args:
        results: Dictionary of analysis results
        filename: Output filename (defaults to config.RESULTS_FILE)
    """
    if filename is None:
        filename = RESULTS_FILE

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("CRYPTOCURRENCY & TECH STOCK ANALYSIS RESULTS\n")
        f.write("=" * 70 + "\n\n")

        # Cross-market correlations
        f.write("CROSS-MARKET CORRELATIONS\n")
        f.write("-" * 70 + "\n")
        f.write("Correlation between cryptocurrency and stock daily returns:\n\n")

        correlations = results['correlations']
        for pair, corr in sorted(correlations.items()):
            f.write(f"  {pair:20s}: {corr:7.4f}\n")

        f.write("\nInterpretation:\n")
        f.write("  1.0 = Perfect positive correlation\n")
        f.write("  0.0 = No correlation\n")
        f.write(" -1.0 = Perfect negative correlation\n")

        # Average volatility
        f.write("\n" + "=" * 70 + "\n")
        f.write("AVERAGE VOLATILITY RANKINGS\n")
        f.write("-" * 70 + "\n\n")

        f.write("Cryptocurrencies:\n")
        for symbol, vol in sorted(results['avg_crypto_volatility'].items(),
                                   key=lambda x: x[1], reverse=True):
            f.write(f"  {symbol:5s}: {vol:6.2f}% average daily volatility\n")

        f.write("\nStocks:\n")
        for symbol, vol in sorted(results['avg_stock_volatility'].items(),
                                   key=lambda x: x[1], reverse=True):
            f.write(f"  {symbol:5s}: {vol:6.2f}% average daily volatility\n")

        # Top momentum days
        f.write("\n" + "=" * 70 + "\n")
        f.write("TOP 5 MOMENTUM DAYS (7-Day Price Change)\n")
        f.write("-" * 70 + "\n\n")

        f.write("Cryptocurrencies:\n")
        for symbol, days in results['top_crypto_momentum'].items():
            f.write(f"\n  {symbol}:\n")
            for date, momentum in days:
                date_str = date_int_to_string(date)
                f.write(f"    {date_str}: {momentum:+7.2f}%\n")

        f.write("\nStocks:\n")
        for symbol, days in results['top_stock_momentum'].items():
            f.write(f"\n  {symbol}:\n")
            for date, momentum in days:
                date_str = date_int_to_string(date)
                f.write(f"    {date_str}: {momentum:+7.2f}%\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("Analysis complete. All data calculated from database SELECT queries.\n")
        f.write("=" * 70 + "\n")

    print(f"\nResults written to: {filename}")


if __name__ == "__main__":
    results = perform_analysis()

    if results:
        write_results_to_file(results)
        print("\n" + "=" * 60)
        print("Analysis complete! Check analysis_results.txt for results.")
        print("=" * 60)
    else:
        print("\nCannot perform analysis - insufficient data.")
        print("Please run data collection scripts first.")
