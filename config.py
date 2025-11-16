# config.py - ТОЛЬКО LIVE РЕЖИМ
from pathlib import Path

ROOT = Path(__file__).parent

# Режим работы
MODE = "live"  # ТОЛЬКО live режим

# Биржа и символ
EXCHANGE = "OKX"
SYMBOL = "BTC-USDT-SWAP"

# Тайминги
BUCKET_SECONDS = 1.0
MIN_SIGNAL_INTERVAL = 30.0
TRADE_HOLD_SECONDS = 60.0

# Параметры стратегии
IMBALANCE_THRESHOLD = 0.62
DELTA_THRESHOLD = 3.0
SPREAD_MAX_PCT = 0.05

# Риск-менеджмент
START_EQUITY = 100.0  # Твоя сумма для расчета позиции
POSITION_PCT = 0.05   # 5% от капитала на сделку

# Директории
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
