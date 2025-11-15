# config.py

# Trading settings
SYMBOL = "BTC-USDT-SWAP"
TIMEFRAME = "1m"

# Data collection
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"
CHANNELS = [
    "books",              # Стакан L2
    "trades",             # Лента сделок
    "tickers"             # Тикеры (funding, OI)
]

# Feature settings
FEATURE_WINDOW = 50

# Model settings
MIN_PROBABILITY = 0.65
