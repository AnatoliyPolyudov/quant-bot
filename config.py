# config.py
SYMBOL = "BTC-USDT-SWAP"
BUCKET_SECONDS = 60.0

# Параметры стратегии
IMBALANCE_THRESHOLD = 0.35
DELTA_THRESHOLD = 8.0

# Фильтры - УМЕНЬШАЕМ для тестирования
MIN_VOLUME = 0.1           # было 10.0 - СЛИШКОМ МНОГО!
CONFIRMATION_PERIODS = 1   # было 2 - для быстрого тестирования