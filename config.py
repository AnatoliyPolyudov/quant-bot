# config.py - ФИКСИРУЕМ ГЛАВНУЮ ПРОБЛЕМУ ВЫХОДОВ
from pathlib import Path

ROOT = Path(__file__).parent

# Режим работы
MODE = "live"  # ТОЛЬКО live режим

# Биржа и символ
EXCHANGE = "OKX"
SYMBOL = "BTC-USDT-SWAP"

# Тайминги ДЛЯ УМНЫХ ВЫХОДОВ
BUCKET_SECONDS = 60.0  # 1 минута анализа
MIN_SIGNAL_INTERVAL = 300.0  # 5 мин между входами (было 180)
TRADE_HOLD_SECONDS = 180.0  # МИНИМУМ 3 минуты удержания (было 300)

# Параметры стратегии - СТРОГИЕ ПОРОГИ
IMBALANCE_THRESHOLD = 0.70  # БЫЛО 0.64 → СЕЙЧАС 0.70
DELTA_THRESHOLD = 8.0  # БЫЛО 4.5 → СЕЙЧАС 8.0
SPREAD_MAX_PCT = 0.03

# Параметры ВЫХОДА - НОВАЯ ЛОГИКА
EXIT_IMBALANCE_THRESHOLD = 0.40  # Жесткий порог выхода
EXIT_DELTA_PER_MINUTE = -5.0  # Скорость разворота для выхода
MIN_HOLD_SECONDS = 120.0  # Минимум 2 минуты удержания

# Риск-менеджмент
START_EQUITY = 100.0
POSITION_PCT = 0.05

# Директории
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
