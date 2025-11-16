# feature_engine.py - ОБНОВЛЕН ДЛЯ 1-МИНУТКИ
from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.delta_deque = deque()
        self.imbalance_history = []  # История имбаланса для 5-минутного усреднения
        self.trade_counts = {"buy": 0, "sell": 0}
        self.last_price = 60000.0
        self.delta_window_sec = 300  # 5 минут для дельты
        self.imbalance_window = 5    # 5 последних значений для усреднения

    def _clean_old(self, now_ts):
        cutoff = now_ts - self.delta_window_sec
        while self.delta_deque and self.delta_deque[0][0] < cutoff:
            self.delta_deque.popleft()

    def _calculate_imbalance(self, bids, asks):
        """Расчет имбаланса из стакана"""
        bid_vol = 0.0
        ask_vol = 0.0
        
        for b in bids[:3]:  # Топ 3 уровня
            try:
                if len(b) >= 2:
                    bid_vol += float(b[1])
            except:
                pass
                
        for a in asks[:3]:  # Топ 3 уровня
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
            
            # Добавляем в историю для усреднения
            self.imbalance_history.append(current_imbalance)
            if len(self.imbalance_history) > self.imbalance_window:
                self.imbalance_history.pop(0)
            
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

        # Усредненный имбаланс за 5 минут
        avg_imbalance = sum(self.imbalance_history) / len(self.imbalance_history) if self.imbalance_history else current_imbalance
        
        # Тренд имбаланса
        imbalance_trend = "rising" if avg_imbalance < current_imbalance else "falling" if avg_imbalance > current_imbalance else "flat"

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
            "avg_imbalance_5min": round(avg_imbalance, 4),  # НОВОЕ: усредненный имбаланс
            "imbalance_trend": imbalance_trend,  # НОВОЕ: тренд имбаланса
            "cumulative_delta": round(cumulative_delta, 6),
            "delta_per_minute": round(delta_per_minute, 2),  # НОВОЕ: скорость дельты
            "spread_percent": round(spread_pct, 6),
            "buy_trades": self.trade_counts["buy"],
            "sell_trades": self.trade_counts["sell"],
            "current_price": round(self.last_price, 2)
        }
        return features

# Global instance
feature_engine = FeatureEngine()
