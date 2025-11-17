# feature_engine.py
from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.delta_deque = deque()
        self.imbalance_history = deque(maxlen=2)
        self.last_price = 60000.0
        self.delta_window_sec = 300  # 5 минут для cumulative_delta
        self.volume_window_sec = 60   # 1 минута для volume_per_minute

    def _clean_old(self, now_ts, window_sec):
        cutoff = now_ts - window_sec
        while self.delta_deque and self.delta_deque[0][0] < cutoff:
            self.delta_deque.popleft()

    def _calculate_imbalance(self, bids, asks):
        bid_vol = sum(float(b[1]) for b in bids[:3] if len(b) >= 2)
        ask_vol = sum(float(a[1]) for a in asks[:3] if len(a) >= 2)
        if (bid_vol + ask_vol) > 0:
            return bid_vol / (bid_vol + ask_vol)
        return 0.5

    def update_from_snapshot(self, snapshot):
        now = time.time()
        ob = snapshot.get("order_book") or {}
        trades = snapshot.get("trades") or []

        current_imbalance = 0.5

        if ob:
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])

            current_imbalance = self._calculate_imbalance(bids, asks)
            self.imbalance_history.append(current_imbalance)

            try:
                if bids and asks:
                    best_bid = float(bids[0][0])
                    best_ask = float(asks[0][0])
                    if best_ask > best_bid:
                        self.last_price = (best_ask + best_bid) / 2
            except:
                pass

        if len(self.imbalance_history) >= 2:
            imb_trend = "rising" if current_imbalance > list(self.imbalance_history)[-2] else "falling"
        else:
            imb_trend = "flat"

        # Добавляем новые трейды
        for t in trades:
            side = t.get("side", "buy")
            sz = float(t.get("sz", 0)) if t.get("sz") else 0.0
            signed = sz if side == "buy" else -sz
            self.delta_deque.append((now, signed))

        # Cumulative Delta (5 минут)
        self._clean_old(now, self.delta_window_sec)
        cumulative_delta = sum(x[1] for x in self.delta_deque)

        # Volume per minute (последняя минута)
        recent_trades = [x for x in self.delta_deque if x[0] > now - 60]
        volume_per_minute = sum(abs(x[1]) for x in recent_trades)

        features = {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(current_imbalance, 4),
            "imbalance_trend": imb_trend,
            "cumulative_delta": round(cumulative_delta, 6),
            "delta_per_minute": round(volume_per_minute, 2),  # Теперь это ОБЪЕМ, а не дельта!
            "current_price": round(self.last_price, 2)
        }
        return features

feature_engine = FeatureEngine()