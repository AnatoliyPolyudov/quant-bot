from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.last_price = 60000.0
        self.imbalance_history = deque(maxlen=2)  # Для тренда

    def _calculate_imbalance(self, bids, asks, levels=3):
        """Расчет имбаланса"""
        levels = min(len(bids), len(asks), levels)
        if levels == 0:
            return 0.5
            
        bid_vol = sum(float(bid[1]) for bid in bids[:levels])
        ask_vol = sum(float(ask[1]) for ask in asks[:levels])
        total = bid_vol + ask_vol
        
        return bid_vol / total if total > 0 else 0.5

    def update_from_snapshot(self, snapshot):
        current_time = time.time()
        ob = snapshot.get("order_book", {})
        
        # Расчет имбаланса
        current_imbalance = 0.5
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])
        
        if bids and asks:
            current_imbalance = self._calculate_imbalance(bids, asks)
            self.imbalance_history.append(current_imbalance)
        
        # Тренд имбаланса
        if len(self.imbalance_history) >= 2:
            trend = "rising" if current_imbalance > self.imbalance_history[-2] else "falling"
        else:
            trend = "flat"

        # Обновление цены
        if bids and asks:
            try:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                if best_ask > best_bid:
                    self.last_price = (best_bid + best_ask) / 2
            except (ValueError, IndexError):
                pass

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(current_imbalance, 4),
            "imbalance_trend": trend,
            "current_price": round(self.last_price, 2)
        }

feature_engine = FeatureEngine()