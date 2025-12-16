"""
Main Project Launcher
SI 201 Final Project: Cryptocurrency & Tech Stock Analysis

This script provides an interactive menu to run all project components.
"""

import os
import sys

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70 + "\n")

def print_menu():
    """Display the main menu"""
    print_header("SI 201 FINAL PROJECT - MAIN MENU")
    print("Current Status:")
    print(f"  Database: {'EXISTS' if os.path.exists('crypto_stock_analysis.db') else 'NOT CREATED'}")
    print(f"  Output folder: {'EXISTS' if os.path.exists('output') else 'NOT CREATED'}")
    print()
    print("Options:")
    print("  1. Initialize Database (Run ONCE at the start)")
    print("  2. Collect Cryptocurrency Data (Run 4-5 times)")
    print("  3. Collect Stock Data (Run 4-5 times)")
    print("  4. Check Data Collection Progress")
    print("  5. Run Analysis (After collecting 100+ rows per source)")
    print("  6. Create Visualizations (After running analysis)")
    print("  7. Run Everything (Steps 2-6 automatically)")
    print("  8. View Database Summary")
    print("  0. Exit")
    print("\n" + "=" * 70)

def initialize_database():
    """Initialize the database"""
    print_header("Step 1: Initialize Database")
    from database_setup import initialize_database as init_db
    init_db()
    print("\nDatabase initialized successfully!")
    input("\nPress Enter to continue...")

def collect_crypto_data():
    """Collect cryptocurrency data"""
    print_header("Step 2: Collect Cryptocurrency Data")
    print("This will fetch data from CoinGecko API (max 25 rows per run)")
    print("Run this script 4-5 times to get 100+ rows per cryptocurrency\n")
    from collect_crypto_data import collect_crypto_data as collect
    collect()
    input("\nPress Enter to continue...")

def collect_stock_data():
    """Collect stock data"""
    print_header("Step 3: Collect Stock Data")
    print("This will fetch data from Alpha Vantage API (max 25 rows per run)")
    print("Run this script 4-5 times to get 100+ rows per stock")
    print("Note: This may take 30-40 seconds due to API rate limits\n")
    from collect_stock_data import collect_stock_data as collect
    collect()
    input("\nPress Enter to continue...")

def check_progress():
    """Check data collection progress"""
    print_header("Data Collection Progress")
    from database_setup import get_crypto_row_count, get_crypto_id, get_stock_row_count, get_stock_id
    from config import CRYPTO_SYMBOLS, STOCK_SYMBOLS

    print("CRYPTOCURRENCY DATA:")
    total_crypto = 0
    for symbol in CRYPTO_SYMBOLS.keys():
        crypto_id = get_crypto_id(symbol)
        if crypto_id:
            count = get_crypto_row_count(crypto_id)
            total_crypto += count
            status = "✓ DONE" if count >= 100 else f"Need {100 - count} more"
            print(f"  {symbol}: {count:4d} rows  [{status}]")
        else:
            print(f"  {symbol}: NOT INITIALIZED")

    print("\nSTOCK DATA:")
    total_stock = 0
    for symbol in STOCK_SYMBOLS:
        stock_id = get_stock_id(symbol)
        if stock_id:
            count = get_stock_row_count(stock_id)
            total_stock += count
            status = "✓ DONE" if count >= 100 else f"Need {100 - count} more"
            print(f"  {symbol}: {count:4d} rows  [{status}]")
        else:
            print(f"  {symbol}: NOT INITIALIZED")

    print(f"\nTOTAL: {total_crypto + total_stock} rows collected")
    print("\nRequirement: 100+ rows for EACH cryptocurrency and stock")

    # Check if all meet requirements
    crypto_ready = all(get_crypto_row_count(get_crypto_id(s)) >= 100 for s in CRYPTO_SYMBOLS.keys() if get_crypto_id(s))
    stock_ready = all(get_stock_row_count(get_stock_id(s)) >= 100 for s in STOCK_SYMBOLS if get_stock_id(s))

    if crypto_ready and stock_ready:
        print("\n✓ ALL DATA COLLECTION COMPLETE! Ready for analysis.")
    elif not crypto_ready:
        print("\n⚠ Need more crypto data. Run 'Collect Cryptocurrency Data' more times.")
    else:
        print("\n⚠ Need more stock data. Run 'Collect Stock Data' more times.")

    input("\nPress Enter to continue...")

def run_analysis():
    """Run data analysis"""
    print_header("Step 5: Run Analysis")
    print("Analyzing data from database...")
    print("This will create: output/analysis_results.txt\n")
    from analyze_data import perform_analysis, write_results_to_file
    results = perform_analysis()

    if results:
        write_results_to_file(results)
        print("\n✓ Analysis complete!")
        print("Results saved to: output/analysis_results.txt")
    else:
        print("\n✗ Analysis failed. Make sure you have collected enough data.")

    input("\nPress Enter to continue...")

def create_visualizations():
    """Create visualizations"""
    print_header("Step 6: Create Visualizations")
    print("Creating visualizations from analyzed data...")
    print("This will create:")
    print("  - output/visualizations/price_movement_chart.png")
    print("  - output/visualizations/correlation_heatmap.png\n")
    from visualize_data import create_all_visualizations
    create_all_visualizations()
    print("\n✓ Visualizations created successfully!")
    input("\nPress Enter to continue...")

def run_everything():
    """Run all steps automatically"""
    print_header("Run Everything Automatically")
    print("This will run data collection multiple times, then analyze and visualize.")
    print("WARNING: This may take 5-10 minutes due to API rate limits.\n")

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        input("\nPress Enter to continue...")
        return

    # Check if database exists
    if not os.path.exists('crypto_stock_analysis.db'):
        print("\nInitializing database first...")
        initialize_database()

    # Collect crypto data 5 times
    print("\nCollecting cryptocurrency data (5 runs)...")
    for i in range(5):
        print(f"\n--- Crypto Collection Run {i+1}/5 ---")
        from collect_crypto_data import collect_crypto_data
        collect_crypto_data()

    # Collect stock data 5 times
    print("\nCollecting stock data (5 runs)...")
    for i in range(5):
        print(f"\n--- Stock Collection Run {i+1}/5 ---")
        from collect_stock_data import collect_stock_data
        collect_stock_data()

    # Check progress
    print("\n" + "=" * 70)
    check_progress()

    # Run analysis
    print("\nRunning analysis...")
    from analyze_data import perform_analysis, write_results_to_file
    results = perform_analysis()
    if results:
        write_results_to_file(results)

    # Create visualizations
    print("\nCreating visualizations...")
    from visualize_data import create_all_visualizations
    create_all_visualizations()

    print("\n" + "=" * 70)
    print("ALL STEPS COMPLETE!")
    print("=" * 70)
    print("\nYour project files are ready:")
    print("  Database: crypto_stock_analysis.db")
    print("  Results:  output/analysis_results.txt")
    print("  Viz 1:    output/visualizations/price_movement_chart.png")
    print("  Viz 2:    output/visualizations/correlation_heatmap.png")

    input("\nPress Enter to continue...")

def view_database_summary():
    """View database summary"""
    print_header("Database Summary")

    if not os.path.exists('crypto_stock_analysis.db'):
        print("Database does not exist yet. Run 'Initialize Database' first.")
        input("\nPress Enter to continue...")
        return

    import sqlite3
    conn = sqlite3.connect('crypto_stock_analysis.db')
    cur = conn.cursor()

    # Show tables
    print("TABLES:")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    for table in tables:
        print(f"  - {table[0]}")

    # Show crypto_symbol table
    print("\nCRYPTO_SYMBOL TABLE:")
    cur.execute("SELECT id, symbol, name FROM crypto_symbol")
    symbols = cur.fetchall()
    for sym in symbols:
        print(f"  ID {sym[0]}: {sym[1]} ({sym[2]})")

    # Show row counts
    print("\nROW COUNTS:")
    cur.execute("SELECT COUNT(*) FROM crypto_symbol")
    print(f"  crypto_symbol: {cur.fetchone()[0]} rows")

    cur.execute("SELECT COUNT(*) FROM crypto_price")
    print(f"  crypto_price:  {cur.fetchone()[0]} rows")

    cur.execute("SELECT COUNT(*) FROM stock_price")
    print(f"  stock_price:   {cur.fetchone()[0]} rows")

    # Show sample data
    print("\nSAMPLE CRYPTO_PRICE DATA (with JOIN):")
    cur.execute("""
        SELECT cs.symbol, cp.date, cp.price_usd
        FROM crypto_price cp
        JOIN crypto_symbol cs ON cp.crypto_id = cs.id
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: ${row[2]:.2f} on {row[1]}")

    print("\nSAMPLE STOCK_PRICE DATA:")
    cur.execute("""
        SELECT symbol, date, close
        FROM stock_price
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: ${row[2]:.2f} on {row[1]}")

    conn.close()
    input("\nPress Enter to continue...")

def main():
    """Main program loop"""
    while True:
        try:
            os.system('clear' if os.name != 'nt' else 'cls')  # Clear screen
            print_menu()
            choice = input("Enter your choice: ")

            if choice == '0':
                print("\nExiting. Good luck with your project!")
                sys.exit(0)
            elif choice == '1':
                initialize_database()
            elif choice == '2':
                collect_crypto_data()
            elif choice == '3':
                collect_stock_data()
            elif choice == '4':
                check_progress()
            elif choice == '5':
                run_analysis()
            elif choice == '6':
                create_visualizations()
            elif choice == '7':
                run_everything()
            elif choice == '8':
                view_database_summary()
            else:
                print("\nInvalid choice. Please try again.")
                input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            sys.exit(0)
        except Exception as e:
            print(f"\n\nError: {e}")
            print("\nIf this persists, check that all required libraries are installed:")
            print("  pip install requests matplotlib seaborn")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    print_header("SI 201 FINAL PROJECT")
    print("Cryptocurrency & Tech Stock Analysis")
    print("\nThis interactive tool will help you:")
    print("  ✓ Collect data from 2 APIs")
    print("  ✓ Store data in SQLite database")
    print("  ✓ Perform calculations with SQL JOINs")
    print("  ✓ Create professional visualizations")
    print("\nMake sure you have installed required libraries:")
    print("  pip install requests matplotlib seaborn")
    input("\nPress Enter to start...")

    main()
