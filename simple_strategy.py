# simple_strategy.py
import time

class SimpleStrategy:
    def __init__(self):
        self.open_position = None

    def analyze(self, features):
        price = features.get("current_price", 0.0)
        delta = features.get("delta", 0)
        abs_up = features.get("absorption_up", False)
        abs_down = features.get("absorption_down", False)

        # LONG сигнал - более чувствительный для M3
        if delta < -0.5 or abs_down:  # было -1.0
            return {
                "action": "ENTER",
                "side": "LONG",
                "price": price,
                "reason": f"absorption_down / delta {delta:.1f}"
            }

        # SHORT сигнал - более чувствительный для M3
        if delta > 0.5 or abs_up:  # было 1.0
            return {
                "action": "ENTER",
                "side": "SHORT",
                "price": price,
                "reason": f"absorption_up / delta {delta:.1f}"
            }

        return {"action": "HOLD", "reason": f"no signal delta {delta:.1f}"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }