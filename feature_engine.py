from collections import deque
import time
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.last_price = 60000.0
        self.recent_trades = deque(maxlen=100)  # Только для объема (последние 100 трейдов)

    def _calculate_imbalance(self, bids, asks, levels=3):
        """Расчет имбаланса с адаптацией к доступным уровням"""
        levels = min(len(bids), len(asks), levels)
        if levels == 0:
            return 0.5
            
        bid_vol = sum(float(bid[1]) for bid in bids[:levels])
        ask_vol = sum(float(ask[1]) for ask in asks[:levels])
        total = bid_vol + ask_vol
        
        return bid_vol / total if total > 0 else 0.5

    def _check_spoofing(self, imbalance, recent_volume, imbalance_threshold=0.65, min_volume=8.0):
        """Простая проверка на спуфинг"""
        is_extreme_imbalance = (imbalance > imbalance_threshold) or (imbalance < (1 - imbalance_threshold))
        
        if is_extreme_imbalance and recent_volume < min_volume:
            return "possible_spoofing"
        return "no_spoofing"

    def _calculate_recent_volume(self, current_time, window_seconds=60):
        """Объем за последние window_seconds секунд"""
        cutoff = current_time - window_seconds
        recent_volume = sum(vol for ts, vol in self.recent_trades if ts > cutoff)
        return recent_volume

    def update_from_snapshot(self, snapshot):
        current_time = time.time()
        ob = snapshot.get("order_book", {})
        trades = snapshot.get("trades", [])
        
        # 1. Обновляем историю объемов для анти-спуфинга
        for trade in trades:
            try:
                volume_str = trade.get("sz", "0")
                volume = float(volume_str) if volume_str else 0.0
                if volume > 0:
                    self.recent_trades.append((current_time, volume))
            except (ValueError, TypeError):
                pass
        
        # 2. Расчет имбаланса
        current_imbalance = 0.5
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])
        
        if bids and asks:
            current_imbalance = self._calculate_imbalance(bids, asks)
        
        # 3. Обновление цены
        if bids and asks:
            try:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                if best_ask > best_bid:
                    self.last_price = (best_bid + best_ask) / 2
            except (ValueError, IndexError):
                pass

        # 4. Проверка на спуфинг
        recent_volume = self._calculate_recent_volume(current_time)
        spoofing_flag = self._check_spoofing(current_imbalance, recent_volume)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(current_imbalance, 4),
            "spoofing_flag": spoofing_flag,
            "current_price": round(self.last_price, 2),
            "recent_volume": round(recent_volume, 2)
        }

feature_engine = FeatureEngine()