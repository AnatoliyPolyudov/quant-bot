# config.py

# Trading settings
SYMBOL = "BTC-USDT-SWAP"
TIMEFRAME = "1m"

# Data collection
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
CHANNELS = [
    "orderBook.400.BTC-USDT-SWAP",
    "trades.BTC-USDT-SWAP", 
    "tickers.BTC-USDT-SWAP"
]

# Feature settings
FEATURE_WINDOW = 50

# Model settings
MIN_PROBABILITY = 0.65
