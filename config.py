# config.py
SYMBOL = "BTC-USDT-SWAP"
BUCKET_SECONDS = 60.0

# Параметры стратегии
IMBALANCE_THRESHOLD = 0.60  # Более чувствительный
DELTA_THRESHOLD = 2.0       # Меньшая дельта

# Фильтры
MIN_VOLUME = 0.5            # Реальный объем для BTC
CONFIRMATION_PERIODS = 1    # Быстрое реагирование