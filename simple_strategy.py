# simple_strategy.py
import time
from config import IMBALANCE_THRESHOLD, DELTA_THRESHOLD, SPREAD_MAX_PCT, MIN_SIGNAL_INTERVAL, TRADE_HOLD_SECONDS

class SimpleStrategy:
    def __init__(self):
        self.last_trade_time = 0
        self.open_position = None  # {"side","entry_ts","entry_price"}

    def can_trade_now(self):
        return (time.time() - self.last_trade_time) >= MIN_SIGNAL_INTERVAL

    def analyze(self, features):
        imb = features.get("order_book_imbalance", 0.5)
        delta = features.get("cumulative_delta", 0.0)
        spread = features.get("spread_percent", 999.0)
        price = features.get("current_price", 0.0)

        # Reject if spread large or malformed
        if spread <= 0 or spread > SPREAD_MAX_PCT:
            return {"action":"HOLD", "reason":"spread_bad", "confidence":0}

        # If open - check exit
        if self.open_position:
            # time exit
            if time.time() - self.open_position["entry_ts"] >= TRADE_HOLD_SECONDS:
                return {"action":"EXIT", "reason":"time_exit", "side": self.open_position["side"], "price": price}
            # reverse condition
            if self.open_position["side"] == "LONG" and (imb < 0.5 or delta < -DELTA_THRESHOLD):
                return {"action":"EXIT", "reason":"reverse", "side":"LONG", "price": price}
            if self.open_position["side"] == "SHORT" and (imb > 0.5 or delta > DELTA_THRESHOLD):
                return {"action":"EXIT", "reason":"reverse", "side":"SHORT", "price": price}
            return {"action":"HOLD", "reason":"position_open", "confidence":0}

        # No open - entry rules
        if imb > IMBALANCE_THRESHOLD and delta > DELTA_THRESHOLD and self.can_trade_now():
            return {"action":"ENTER", "side":"LONG", "price": price, "confidence":80, "reason":"imb_delta_long"}
        if imb < (1.0 - IMBALANCE_THRESHOLD) and delta < -DELTA_THRESHOLD and self.can_trade_now():
            return {"action":"ENTER", "side":"SHORT", "price": price, "confidence":80, "reason":"imb_delta_short"}

        return {"action":"HOLD", "reason":"no_signal", "confidence":0}

    def record_entry(self, side, price):
        self.open_position = {"side": side, "entry_ts": time.time(), "entry_price": price}
        self.last_trade_time = time.time()

    def record_exit(self):
        self.open_position = None
        self.last_trade_time = time.time()
