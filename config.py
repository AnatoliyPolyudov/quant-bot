# config.py - Quantum Bot LITE v1.0 (live-capable, demo by default)
from pathlib import Path

ROOT = Path(__file__).parent

# MODE: "demo" or "live" or "sandbox"
MODE = "demo"            # demo = synthetic data; sandbox/live require keys and adjustments

# Exchange / symbol
EXCHANGE = "OKX"
SYMBOL = "BTC-USDT-SWAP"  # OKX perpetual contract id

# Timing
BUCKET_SECONDS = 1.0         # feature aggregation bucket (seconds)
MIN_SIGNAL_INTERVAL = 30.0   # minimum seconds between real trade signals (protect human)
TRADE_HOLD_SECONDS = 60.0    # time-based exit (seconds)

# Strategy thresholds (tuneable)
IMBALANCE_THRESHOLD = 0.62   # bid/(bid+ask) threshold for long
DELTA_THRESHOLD = 3.0        # rolling signed volume threshold
SPREAD_MAX_PCT = 0.05        # max spread percent allowed (in percent)

# Execution / risk
RISK_PER_TRADE_PCT = 0.3     # percent of equity risked per trade (paper)
START_EQUITY = 70.0          # starting equity default — set to your actual balance for sizing
POSITION_PCT = 0.05          # fraction of equity per position (5% of equity)

# Target / logging
TARGET_HORIZON_SEC = 8
TARGET_THRESHOLD_PCT = 0.03  # 0.03% move considered significant

# Demo generator settings (used in demo MODE)
DEMO_PRICE = 60000.0
DEMO_VOL = 2.0               # price volatility scale

# Windows (fallback)
WINDOWS = {
    "delta_window_sec": 30,
    "volatility_window_sec": 120,
    "depth_aggregation_sec": 3,
    "oi_window_sec": 300
}

# Files & dirs
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"
MODELS_DIR = ROOT / "models"

for d in (DATA_DIR, LOGS_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)
