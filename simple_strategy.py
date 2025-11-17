from config import IMBALANCE_THRESHOLD

class SimpleStrategy:
    def __init__(self):
        self.open_position = None

    def analyze(self, features):
        imb = features.get("order_book_imbalance", 0.5)
        spoofing = features.get("spoofing_flag", "no_spoofing")
        price = features.get("current_price", 0.0)

        if self.open_position is not None:
            return {"action": "HOLD", "reason": "position_open"}

        # Проверяем спуфинг
        if spoofing == "possible_spoofing":
            return {"action": "HOLD", "reason": "possible_spoofing"}

        # LONG сигнал
        if imb > IMBALANCE_THRESHOLD:
            return {
                "action": "ENTER", 
                "side": "LONG", 
                "price": price,
                "reason": "buy_pressure"
            }

        # SHORT сигнал  
        if imb < (1 - IMBALANCE_THRESHOLD):
            return {
                "action": "ENTER",
                "side": "SHORT", 
                "price": price,
                "reason": "sell_pressure"
            }

        return {"action": "HOLD", "reason": "no_imbalance"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }