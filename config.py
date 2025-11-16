# config.py - ТОЛЬКО LIVE РЕЖИМ
from pathlib import Path

ROOT = Path(__file__).parent

# Режим работы
MODE = "live"  # ТОЛЬКО live режим

# Биржа и символ
EXCHANGE = "OKX"
SYMBOL = "BTC-USDT-SWAP"

# Тайминги ДЛЯ 1-МИНУТНОГО АНАЛИЗА
BUCKET_SECONDS = 60.0  # БЫЛО 1.0 → СЕЙЧАС 60.0 (1 минута)
MIN_SIGNAL_INTERVAL = 180.0  # БЫЛО 30.0 → СЕЙЧАС 180.0 (3 мин между входами)
TRADE_HOLD_SECONDS = 300.0  # БЫЛО 60.0 → СЕЙЧАС 300.0 (5 минут удержание)

# Параметры стратегии ДЛЯ 1-МИНУТКИ
IMBALANCE_THRESHOLD = 0.64  # БЫЛО 0.62 → Более строгий порог
DELTA_THRESHOLD = 4.5  # БЫЛО 3.0 → Более сильный поток
SPREAD_MAX_PCT = 0.03  # БЫЛО 0.05 → Более жесткий спред

# Риск-менеджмент
START_EQUITY = 100.0  # Твоя сумма для расчета позиции
POSITION_PCT = 0.05   # 5% от капитала на сделку

# Директории
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
