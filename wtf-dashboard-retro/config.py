import os

# Dashboard Configuration
# Edit these values to customize your dashboard
# Secrets are loaded from environment variables with fallback to empty string.
# Set them via: set WEATHER_API_KEY=your_key  (Windows)

# Weather — get a free API key at openweathermap.org/api
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "72ec8dea6854e1ae1cc0e0d5971b9e27")
WEATHER_CITIES = [
    "Talsi,LV",
    "Riga,LV",
    "London,GB",
    "Berlin,DE",
    "Rome,IT",
    "Dubai,AE",
    "Sydney,AU",
    "Los Angeles,US",
    "New York,US",
]

# Countdown
COUNTDOWN_DATE = "2026-12-31"
COUNTDOWN_LABEL = "Year End"

# Timer alert sound — path to a .wav file, or "" for no sound
TIMER_SOUND = ""  # e.g. r"C:\Users\Arturs\Music\alert.wav"

# News
RSS_URL = "https://feeds.feedburner.com/TechCrunch"
REDDIT_SUBS = ["technology", "artificial"]

# Custom shell command shown in Screen 3
# WARNING: CUSTOM_COMMAND_SHELL=True passes command to the OS shell (supports pipes, &&).
# Set to False and avoid shell metacharacters if the command doesn't need shell features.
CUSTOM_COMMAND = 'echo uptime: && python -c "import time; print(time.strftime(\'%H:%M:%S\'))"'
CUSTOM_COMMAND_SHELL = True

# Stocks
INDEX_TICKERS = ["^GSPC", "^DJI", "^NDX"]
INDEX_NAMES = {"^GSPC": "S&P 500", "^DJI": "DJIA", "^NDX": "NASDAQ-100"}

SP500_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "BRK-B", "LLY", "AVGO"]

# Crypto (CoinGecko IDs)
CRYPTO_IDS = [
    "bitcoin", "ethereum", "tether", "binancecoin", "ripple",
    "usd-coin", "solana", "tron", "dogecoin", "cardano"
]
CRYPTO_SYMBOLS = {
    "bitcoin": "BTC", "ethereum": "ETH", "tether": "USDT",
    "binancecoin": "BNB", "ripple": "XRP", "usd-coin": "USDC",
    "solana": "SOL", "tron": "TRX", "dogecoin": "DOGE", "cardano": "ADA"
}

# World clocks (timezone, display name)
WORLD_CLOCKS = [
    ("Europe/Riga",        "RIGA"),
    ("Europe/London",      "LONDON"),
    ("Europe/Berlin",      "BERLIN"),
    ("Europe/Rome",        "ROME"),
    ("Asia/Dubai",         "DUBAI"),
    ("Australia/Sydney",   "SYDNEY"),
    ("America/Los_Angeles","LA"),
    ("America/New_York",   "NEW YORK"),
]

# Todo file path
TODO_FILE = "todo.txt"

# LibreHardwareMonitor web server URL (Options → Web Server in LHM)
LHM_URL = "http://localhost:8085/data.json"

# Screen 4 — Home Lab
GITHUB_USERNAME = ""           # e.g. "arturs123"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # optional, increases rate limit
LAT = 56.9496                  # Latitude for sunrise/sunset (Riga default)
LON = 24.1052                  # Longitude

# Screen 5 — Finance
TOGGL_API_TOKEN = os.environ.get("TOGGL_API_TOKEN", "")  # from toggl.com/profile
EXCHANGE_BASE = "EUR"
EXCHANGE_CURRENCIES = ["USD", "GBP", "RUB", "CHF", "JPY", "SEK", "NOK"]

# News filter
NEWS_FILTER_KEYWORDS = ["AI", "Python", "Latvia", "GPU"]
