# feature_engine.py - УПРОЩЕННАЯ ВЕРСИЯ
from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.delta_deque = deque()
        self.trade_counts = {"buy": 0, "sell": 0}
        self.last_price = 60000.0
        self.delta_window_sec = 30  # Просто фиксированное значение

    def _clean_old(self, now_ts):
        cutoff = now_ts - self.delta_window_sec
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
            
            # Calculate imbalance from top 3 levels
            bid_vol = 0.0
            ask_vol = 0.0
            
            for b in bids[:3]:
                try:
                    if len(b) >= 2:
                        bid_vol += float(b[1])
                except:
                    pass
                    
            for a in asks[:3]:
                try:
                    if len(a) >= 2:
                        ask_vol += float(a[1])
                except:
                    pass
                    
            if (bid_vol + ask_vol) > 0:
                imbalance = bid_vol / (bid_vol + ask_vol)
            
            # Calculate spread
            try:
                if bids and asks:
                    best_bid = float(bids[0][0])
                    best_ask = float(asks[0][0])
                    if best_ask > best_bid:
                        spread_pct = (best_ask - best_bid) / ((best_ask + best_bid) / 2) * 100.0
                        self.last_price = (best_ask + best_bid) / 2
            except:
                pass

        # Update delta from trades
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

        # Clean old trades and calculate cumulative delta
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

# Global instance
feature_engine = FeatureEngine()
