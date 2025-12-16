"""
Configuration file for API keys and project settings
"""

# Alpha Vantage API Configuration
# Get your free API key at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY = "AKTPHZ9R94F6893U"

# CoinGecko API Configuration
# No API key required for free tier
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Alpha Vantage API Configuration
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Database Configuration
DATABASE_NAME = "crypto_stock_analysis.db"

# Data Collection Configuration
MAX_ROWS_PER_RUN = 25  # Maximum rows to insert per execution

# Cryptocurrency Configuration
CRYPTO_SYMBOLS = {
    'BTC': {'coingecko_id': 'bitcoin', 'name': 'Bitcoin'},
    'ETH': {'coingecko_id': 'ethereum', 'name': 'Ethereum'},
    'SOL': {'coingecko_id': 'solana', 'name': 'Solana'}
}

# Stock Configuration
STOCK_SYMBOLS = ['NVDA', 'AMD', 'COIN']

# Output Configuration
OUTPUT_DIR = "output"
VISUALIZATIONS_DIR = f"{OUTPUT_DIR}/visualizations"
RESULTS_FILE = f"{OUTPUT_DIR}/analysis_results.txt"
