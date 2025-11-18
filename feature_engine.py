# feature_engine.py
from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.last_price = 60000.0
        self.imbalance_history = deque(maxlen=2)
        self.trade_history = deque()
        self.price_history = deque()

    def _calculate_imbalance(self, bids, asks, levels=3):
        """Расчет имбаланса"""
        levels = min(len(bids), len(asks), levels)
        if levels == 0:
            return 0.5
            
        bid_vol = sum(float(bid[1]) for bid in bids[:levels])
        ask_vol = sum(float(ask[1]) for ask in asks[:levels])
        total = bid_vol + ask_vol
        
        return bid_vol / total if total > 0 else 0.5

    def update_trades(self, trades):
        """Обновление истории трейдов"""
        ts = time.time()
        for trade in trades:
            side = trade.get("side", "buy")
            volume = float(trade.get("sz", 0))
            self.trade_history.append((ts, side, volume))
        self.price_history.append((ts, self.last_price))

    def compute_delta_absorption(self, window=60):  # УВЕЛИЧЕНО до 60 секунд
        """Считаем дельту и absorption"""
        now = time.time()
        while self.trade_history and self.trade_history[0][0] < now - window:
            self.trade_history.popleft()
        while self.price_history and self.price_history[0][0] < now - window:
            self.price_history.popleft()

        delta = sum(v for t,s,v in self.trade_history if s=="buy") - sum(v for t,s,v in self.trade_history if s=="sell")
        price_change = self.last_price - self.price_history[0][1] if self.price_history else 0

        absorption_up = price_change > 0 and delta <= 0
        absorption_down = price_change < 0 and delta >= 0

        return {
            "delta": delta,
            "price_change": price_change,
            "absorption_up": absorption_up,
            "absorption_down": absorption_down
        }

    def update_from_snapshot(self, snapshot):
        current_time = time.time()
        ob = snapshot.get("order_book", {})
        trades = snapshot.get("trades", [])

        bids = ob.get("bids", [])
        asks = ob.get("asks", [])
        if bids and asks:
            try:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                if best_ask > best_bid:
                    self.last_price = (best_bid + best_ask) / 2
            except (ValueError, IndexError):
                pass

        current_imbalance = 0.5
        if bids and asks:
            current_imbalance = self._calculate_imbalance(bids, asks)
            self.imbalance_history.append(current_imbalance)

        if len(self.imbalance_history) >= 2:
            trend = "rising" if current_imbalance > self.imbalance_history[-2] else "falling"
        else:
            trend = "flat"

        self.update_trades(trades)
        abs_features = self.compute_delta_absorption(window=60)  # 60 секунд для надежности

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(current_imbalance, 4),
            "imbalance_trend": trend,
            "current_price": round(self.last_price, 2),
            **abs_features
        }

feature_engine = FeatureEngine()