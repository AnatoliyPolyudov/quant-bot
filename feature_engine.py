# feature_engine.py - БЫСТРЫЙ ТРЕНД ДЛЯ 2 МИНУТ
from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.delta_deque = deque()
        self.imbalance_history = deque(maxlen=2)  # ТОЛЬКО 2 последних значения для быстрого тренда
        self.trade_counts = {"buy": 0, "sell": 0}
        self.last_price = 60000.0
        self.delta_window_sec = 300  # 5 минут для дельты

    def _clean_old(self, now_ts):
        cutoff = now_ts - self.delta_window_sec
        while self.delta_deque and self.delta_deque[0][0] < cutoff:
            self.delta_deque.popleft()

    def _calculate_imbalance(self, bids, asks):
        """Расчет имбаланса из стакана"""
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
            return bid_vol / (bid_vol + ask_vol)
        return 0.5

    def update_from_snapshot(self, snapshot):
        now = time.time()
        ob = snapshot.get("order_book") or {}
        trades = snapshot.get("trades") or []

        # Imbalance and spread
        current_imbalance = 0.5
        spread_pct = 0.0
        
        if ob:
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            
            # Calculate current imbalance
            current_imbalance = self._calculate_imbalance(bids, asks)
            
            # Сохраняем для быстрого тренда (2 значения)
            self.imbalance_history.append(current_imbalance)
            
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

        # БЫСТРЫЙ ТРЕНД - по 2 последним значениям
        if len(self.imbalance_history) >= 2:
            imb_trend = "rising" if current_imbalance > list(self.imbalance_history)[-2] else "falling"
        else:
            imb_trend = "flat"

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
        
        # Дельта в минуту (нормализация)
        delta_per_minute = cumulative_delta / 5.0 if cumulative_delta != 0 else 0.0

        features = {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(current_imbalance, 4),
            "imbalance_trend": imb_trend,  # БЫСТРЫЙ тренд
            "cumulative_delta": round(cumulative_delta, 6),
            "delta_per_minute": round(delta_per_minute, 2),
            "spread_percent": round(spread_pct, 6),
            "buy_trades": self.trade_counts["buy"],
            "sell_trades": self.trade_counts["sell"],
            "current_price": round(self.last_price, 2)
        }
        return features

# Global instance
feature_engine = FeatureEngine()
