"""
Data Visualization Module
Creates visualizations from calculated data
Requires: matplotlib and seaborn
"""

import matplotlib.pyplot as plt
import seaborn as sns
from analyze_data import perform_analysis
from database_setup import get_db_connection, date_int_to_string
from config import VISUALIZATIONS_DIR
import numpy as np
import os
from datetime import datetime


def get_normalized_prices():
    """
    Get price data normalized to starting value of 100
    Uses JOIN to get crypto symbol names

    Returns:
        tuple: (crypto_normalized, stock_normalized, dates)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Get crypto prices with JOIN
    crypto_query = """
        SELECT
            cp.date,
            cs.symbol,
            cp.price_usd
        FROM crypto_price cp
        JOIN crypto_symbol cs ON cp.crypto_id = cs.id
        ORDER BY cs.symbol, cp.date
    """

    cur.execute(crypto_query)
    crypto_rows = cur.fetchall()

    # Get stock prices with JOIN
    stock_query = """
        SELECT sp.date, ss.symbol, sp.close
        FROM stock_price sp
        JOIN stock_symbol ss ON sp.stock_id = ss.id
        ORDER BY ss.symbol, sp.date
    """

    cur.execute(stock_query)
    stock_rows = cur.fetchall()

    conn.close()

    # Organize by symbol
    crypto_by_symbol = {}
    for row in crypto_rows:
        symbol = row['symbol']
        if symbol not in crypto_by_symbol:
            crypto_by_symbol[symbol] = []
        crypto_by_symbol[symbol].append((row['date'], row['price_usd']))

    stock_by_symbol = {}
    for row in stock_rows:
        symbol = row['symbol']
        if symbol not in stock_by_symbol:
            stock_by_symbol[symbol] = []
        stock_by_symbol[symbol].append((row['date'], row['close']))

    # Normalize to 100
    crypto_normalized = {}
    for symbol, data in crypto_by_symbol.items():
        if data:
            first_price = data[0][1]
            normalized = [(date, (price / first_price) * 100) for date, price in data]
            crypto_normalized[symbol] = normalized

    stock_normalized = {}
    for symbol, data in stock_by_symbol.items():
        if data:
            first_price = data[0][1]
            normalized = [(date, (price / first_price) * 100) for date, price in data]
            stock_normalized[symbol] = normalized

    return crypto_normalized, stock_normalized


def create_price_movement_chart():
    """
    Visualization 1: Dual-axis line chart showing normalized price movements
    Cryptocurrencies on left axis, stocks on right axis
    """
    print("Creating Visualization 1: Price Movement Chart...")

    crypto_normalized, stock_normalized = get_normalized_prices()

    if not crypto_normalized or not stock_normalized:
        print("Error: Not enough data for visualization")
        return

    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Get all unique dates and convert to datetime for proper plotting
    all_dates = set()
    for data in crypto_normalized.values():
        all_dates.update([d for d, _ in data])
    for data in stock_normalized.values():
        all_dates.update([d for d, _ in data])

    # Convert integer dates to datetime objects
    date_mapping = {}
    for date_int in sorted(all_dates):
        date_str = date_int_to_string(date_int)
        date_mapping[date_int] = datetime.strptime(date_str, '%Y-%m-%d')

    # Plot cryptocurrencies on left axis
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Cryptocurrency Index (Base = 100)', fontsize=12, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    crypto_colors = {'BTC': '#f7931a', 'ETH': '#627eea', 'SOL': '#00ffbd'}
    crypto_styles = {'BTC': '-', 'ETH': '--', 'SOL': '-.'}

    for symbol, data in crypto_normalized.items():
        # Convert integer dates to datetime objects
        dates_dt = [date_mapping[d] for d, _ in data]
        values = [v for _, v in data]
        color = crypto_colors.get(symbol, 'blue')
        style = crypto_styles.get(symbol, '-')
        ax1.plot(dates_dt, values, label=f'{symbol} (Crypto)',
                linestyle=style, linewidth=2, color=color, alpha=0.8)

    # Create second y-axis for stocks
    ax2 = ax1.twinx()
    ax2.set_ylabel('Stock Index (Base = 100)', fontsize=12, color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    stock_colors = {'NVDA': '#76b900', 'AMD': '#ed1c24', 'COIN': '#0052ff'}
    stock_styles = {'NVDA': '-', 'AMD': '--', 'COIN': ':'}

    for symbol, data in stock_normalized.items():
        # Convert integer dates to datetime objects
        dates_dt = [date_mapping[d] for d, _ in data]
        values = [v for _, v in data]
        color = stock_colors.get(symbol, 'red')
        style = stock_styles.get(symbol, '-')
        ax2.plot(dates_dt, values, label=f'{symbol} (Stock)',
                linestyle=style, linewidth=2, color=color, alpha=0.8)

    # Format x-axis to show dates nicely
    import matplotlib.dates as mdates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())

    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right')

    # Add title and legends
    plt.title('Cryptocurrency vs Tech Stock Price Movements\n(Normalized to Base 100)',
              fontsize=14, fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
              loc='upper left', fontsize=10, framealpha=0.9)

    # Add grid for readability
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()

    # Create output directory if it doesn't exist
    os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)

    filepath = os.path.join(VISUALIZATIONS_DIR, 'price_movement_chart.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  Saved: {filepath}")

    plt.show()


def create_correlation_heatmap(results):
    """
    Visualization 2: Correlation heatmap showing relationships
    between all cryptocurrencies and stocks
    """
    print("Creating Visualization 2: Correlation Heatmap...")

    correlations = results['correlations']

    if not correlations:
        print("Error: No correlation data available")
        return

    # Extract unique symbols
    crypto_symbols = set()
    stock_symbols = set()

    for pair in correlations.keys():
        crypto, stock = pair.split('-')
        crypto_symbols.add(crypto)
        stock_symbols.add(stock)

    crypto_symbols = sorted(crypto_symbols)
    stock_symbols = sorted(stock_symbols)

    # Create correlation matrix
    matrix = np.zeros((len(crypto_symbols), len(stock_symbols)))

    for i, crypto in enumerate(crypto_symbols):
        for j, stock in enumerate(stock_symbols):
            pair = f"{crypto}-{stock}"
            matrix[i, j] = correlations.get(pair, 0)

    # Create heatmap
    plt.figure(figsize=(10, 8))

    # Use custom colormap: red for negative, white for zero, green for positive
    sns.heatmap(matrix,
                annot=True,  # Show correlation values
                fmt='.3f',   # Format to 3 decimal places
                cmap='RdYlGn',  # Red-Yellow-Green colormap
                center=0,    # Center colormap at zero
                vmin=-1,     # Min correlation value
                vmax=1,      # Max correlation value
                xticklabels=stock_symbols,
                yticklabels=crypto_symbols,
                cbar_kws={'label': 'Correlation Coefficient'},
                linewidths=0.5,
                linecolor='gray')

    plt.title('Cross-Market Correlation Heatmap\n' +
              'Cryptocurrency Daily Returns vs Tech Stock Daily Returns',
              fontsize=14, fontweight='bold', pad=20)

    plt.xlabel('Stock Symbols', fontsize=12, fontweight='bold')
    plt.ylabel('Cryptocurrency Symbols', fontsize=12, fontweight='bold')

    # Rotate labels for better readability
    plt.xticks(rotation=0, fontsize=11)
    plt.yticks(rotation=0, fontsize=11)

    plt.tight_layout()

    # Create output directory if it doesn't exist
    os.makedirs(VISUALIZATIONS_DIR, exist_ok=True)

    filepath = os.path.join(VISUALIZATIONS_DIR, 'correlation_heatmap.png')
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"  Saved: {filepath}")

    plt.show()


def create_all_visualizations():
    """
    Main function to create all required visualizations
    """
    print("=" * 60)
    print("Creating Visualizations")
    print("=" * 60)

    # Check if matplotlib and seaborn are available
    try:
        import matplotlib
        import seaborn
        print("\nRequired libraries found: matplotlib, seaborn")
    except ImportError as e:
        print(f"\nError: Missing required library: {e}")
        print("Please install: pip install matplotlib seaborn")
        return

    # Get analysis results
    print("\nPerforming analysis...")
    results = perform_analysis()

    if not results:
        print("\nError: Could not perform analysis")
        print("Make sure you have collected enough data first.")
        return

    print("\n" + "-" * 60)

    # Create visualization 1
    try:
        create_price_movement_chart()
    except Exception as e:
        print(f"Error creating price movement chart: {e}")

    print("-" * 60)

    # Create visualization 2
    try:
        create_correlation_heatmap(results)
    except Exception as e:
        print(f"Error creating correlation heatmap: {e}")

    print("\n" + "=" * 60)
    print("Visualization creation complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  1. price_movement_chart.png - Dual-axis price movements")
    print("  2. correlation_heatmap.png - Cross-market correlations")
    print("\nThese visualizations are different from lecture examples:")
    print("  - Uses dual y-axis (not shown in lecture)")
    print("  - Custom color schemes for each asset")
    print("  - Correlation heatmap (not basic bar/line charts)")
    print("=" * 60)


if __name__ == "__main__":
    create_all_visualizations()
