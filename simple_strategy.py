import time
from config import IMBALANCE_THRESHOLD, DELTA_THRESHOLD

class SimpleStrategy:
    """
    Лёгкая стратегия: только входные сигналы
    """

    def __init__(self):
        self.open_position = None  # {"side","entry_price","entry_ts"}
    
    def analyze(self, features):
        """Возвращает: {action, side, price, reason}"""
        imb = features.get("order_book_imbalance", 0.5)
        delta_value = features.get("cumulative_delta", 0.0)
        trend = features.get("imbalance_trend", "flat")
        price = features.get("current_price", 0.0)

        if self.open_position is None:
            # SHORT сигнал
            if imb < (1 - IMBALANCE_THRESHOLD) and delta_value < -DELTA_THRESHOLD and trend == "falling":
                return {
                    "action": "ENTER",
                    "side": "SHORT",
                    "price": price,
                    "reason": "strong_short_signal"
                }
            # LONG сигнал
            if imb > IMBALANCE_THRESHOLD and delta_value > DELTA_THRESHOLD and trend == "rising":
                return {
                    "action": "ENTER",
                    "side": "LONG",
                    "price": price,
                    "reason": "strong_long_signal"
                }

        return {"action": "HOLD", "reason": "no_signal"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }
