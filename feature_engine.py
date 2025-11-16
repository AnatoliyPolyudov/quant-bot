# feature_engine.py
# Compute 3 features: imbalance (top3), rolling cumulative delta, spread_percent
from collections import deque
import time
from datetime import datetime
from config import WINDOWS, DEMO_PRICE

DELTA_WINDOW_SEC = WINDOWS.get("delta_window_sec", 30)

class FeatureEngine:
    def __init__(self):
        self.delta_deque = deque()
        self.trade_counts = {"buy":0, "sell":0}
        self.last_price = DEMO_PRICE

    def _clean_old(self, now_ts):
        cutoff = now_ts - DELTA_WINDOW_SEC
        while self.delta_deque and self.delta_deque[0][0] < cutoff:
            self.delta_deque.popleft()

    def update_from_snapshot(self, snapshot):
        now = time.time()
        ob = snapshot.get("order_book") or {}
        trades = snapshot.get("trades") or []

        # Imbalance and spread
        imbalance = 0.5
        spread_pct = 0.0
        if ob:
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            bid_vol = sum(float(b[1]) for b in bids[:3] if len(b)>=2)
            ask_vol = sum(float(a[1]) for a in asks[:3] if len(a)>=2)
            if (bid_vol + ask_vol) > 0:
                imbalance = bid_vol / (bid_vol + ask_vol)
            try:
                best_bid = float(bids[0][0]) if bids else None
                best_ask = float(asks[0][0]) if asks else None
                if best_bid and best_ask and best_ask > best_bid:
                    spread_pct = (best_ask - best_bid) / ((best_ask + best_bid)/2) * 100.0
                self.last_price = (best_ask + best_bid)/2
            except:
                pass

        # Update delta deque
        for t in trades:
            side = t.get("side", "buy")
            try:
                sz = float(t.get("sz", 0))
            except:
                sz = 0.0
            signed = sz if side == "buy" else -sz
            self.delta_deque.append((now, signed))
            if side == "buy":
                self.trade_counts["buy"] += 1
            else:
                self.trade_counts["sell"] += 1

        self._clean_old(now)
        cumulative_delta = sum(x[1] for x in self.delta_deque)

        features = {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(imbalance, 4),
            "spread_percent": round(spread_pct, 6),
            "cumulative_delta": round(cumulative_delta, 6),
            "buy_trades": self.trade_counts["buy"],
            "sell_trades": self.trade_counts["sell"],
            "current_price": round(self.last_price, 2)
        }
        return features

# global instance
feature_engine = FeatureEngine()
