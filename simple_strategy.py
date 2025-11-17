import time
from config import IMBALANCE_THRESHOLD

class SimpleStrategy:
    def __init__(self):
        self.open_position = None

    def analyze(self, features):
        imb = features.get("order_book_imbalance", 0.5)
        trend = features.get("imbalance_trend", "flat")
        price = features.get("current_price", 0.0)

        if self.open_position is not None:
            return {"action": "HOLD", "reason": "position_open"}

        # LONG сигнал
        if imb > IMBALANCE_THRESHOLD and trend == "rising":
            return {
                "action": "ENTER", 
                "side": "LONG", 
                "price": price,
                "reason": "strong_buy_pressure"
            }

        # SHORT сигнал  
        if imb < (1 - IMBALANCE_THRESHOLD) and trend == "falling":
            return {
                "action": "ENTER",
                "side": "SHORT", 
                "price": price,
                "reason": "strong_sell_pressure"
            }

        return {"action": "HOLD", "reason": f"no_signal imb:{imb:.3f} trend:{trend}"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }