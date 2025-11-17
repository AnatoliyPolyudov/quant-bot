import time
from config import IMBALANCE_THRESHOLD

class SimpleStrategy:
    def __init__(self):
        self.open_position = None

    def analyze(self, features):
        imb = features.get("order_book_imbalance", 0.5)
        trend = features.get("imbalance_trend", "flat")
        price = features.get("current_price", 0.0)
        delta = features.get("delta", 0)
        abs_up = features.get("absorption_up", False)
        abs_down = features.get("absorption_down", False)

        if self.open_position is not None:
            return {"action": "HOLD", "reason": "position_open"}

        # LONG сигнал
        if imb > IMBALANCE_THRESHOLD and trend == "rising" and not abs_up and delta > 5:
            return {
                "action": "ENTER", 
                "side": "LONG", 
                "price": price,
                "reason": "strong_buy_pressure"
            }

        # SHORT сигнал  
        if imb < (1 - IMBALANCE_THRESHOLD) and trend == "falling" and not abs_down and delta < -5:
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
