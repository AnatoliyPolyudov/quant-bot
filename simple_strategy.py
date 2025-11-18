import time

class SimpleStrategy:
    def __init__(self):
        self.open_position = None

    def analyze(self, features):
        price = features.get("current_price", 0.0)
        delta = features.get("delta", 0)
        abs_up = features.get("absorption_up", False)
        abs_down = features.get("absorption_down", False)

        # LONG сигнал (разворот после SFP/поглощения снизу)
        if abs_down or (delta < -1):
            return {
                "action": "ENTER",
                "side": "LONG",
                "price": price,
                "reason": f"absorption_down / delta {delta}"
            }

        # SHORT сигнал (разворот после SFP/поглощения сверху)
        if abs_up or (delta > 1):
            return {
                "action": "ENTER",
                "side": "SHORT",
                "price": price,
                "reason": f"absorption_up / delta {delta}"
            }

        return {"action": "HOLD", "reason": f"no signal delta {delta}"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }
