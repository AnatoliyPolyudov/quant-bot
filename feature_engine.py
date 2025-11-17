from collections import deque
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FeatureEngine:
    def __init__(self):
        self.trade_history = deque()  # (timestamp, side, volume)
        self.imbalance_history = deque(maxlen=3)
        self.last_price = 60000.0
        self.window_seconds = 300  # 5 минут для анализа

    def _clean_old_trades(self, current_time):
        """Очистка старых трейдов с проверкой временных меток"""
        cutoff = current_time - self.window_seconds
        initial_count = len(self.trade_history)
        
        while self.trade_history and self.trade_history[0][0] < cutoff:
            self.trade_history.popleft()
            
        if initial_count > 0 and len(self.trade_history) == 0:
            logger.debug("All trades cleared from history")

    def _calculate_imbalance(self, bids, asks, levels=3):
        """Расчет имбаланса с проверкой достаточности данных"""
        try:
            # Проверяем, что есть достаточно уровней в стакане
            if len(bids) < levels or len(asks) < levels:
                logger.warning(f"Insufficient order book levels: bids={len(bids)}, asks={len(asks)}")
                levels = min(len(bids), len(asks))
                if levels == 0:
                    return 0.5
            
            bid_vol = sum(float(bid[1]) for bid in bids[:levels])
            ask_vol = sum(float(ask[1]) for ask in asks[:levels])
            total = bid_vol + ask_vol
            
            if total <= 0:
                logger.warning("Zero total volume in order book")
                return 0.5
                
            imbalance = bid_vol / total
            return imbalance
            
        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"Error calculating imbalance: {e}")
            return 0.5

    def _calculate_trend(self, current_imbalance):
        """Расчет тренда имбаланса с обработкой равенства"""
        if len(self.imbalance_history) < 2:
            return "flat"
        
        prev_imbalance = self.imbalance_history[-1]
        
        if current_imbalance > prev_imbalance:
            return "rising"
        elif current_imbalance < prev_imbalance:
            return "falling"
        else:
            return "flat"

    def _update_price(self, bids, asks):
        """Обновление цены с обработкой ошибок"""
        try:
            if not bids or not asks:
                logger.warning("Empty bids or asks in order book")
                return
                
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            
            if best_ask <= best_bid:
                logger.warning(f"Invalid spread: bid={best_bid}, ask={best_ask}")
                return
                
            self.last_price = (best_bid + best_ask) / 2
            
        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"Error updating price: {e}")

    def update_from_snapshot(self, snapshot):
        current_time = time.time()
        ob = snapshot.get("order_book", {})
        trades = snapshot.get("trades", [])
        
        # 1. Расчет имбаланса
        current_imbalance = 0.5
        bids = ob.get("bids", [])
        asks = ob.get("asks", [])
        
        if bids and asks:
            current_imbalance = self._calculate_imbalance(bids, asks)
            self.imbalance_history.append(current_imbalance)
        
        # 2. Обновление истории трейдов
        valid_trades_count = 0
        for trade in trades:
            try:
                side = trade.get("side", "").lower()
                volume_str = trade.get("sz", "0")
                volume = float(volume_str) if volume_str else 0.0
                
                if side in ["buy", "sell"] and volume > 0:
                    self.trade_history.append((current_time, side, volume))
                    valid_trades_count += 1
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid trade data: {trade}, error: {e}")
        
        # 3. Очистка старых трейдов
        self._clean_old_trades(current_time)
        
        # 4. Расчет метрик
        # Кумулятивная дельта за 5 минут
        buy_volume = sum(vol for ts, side, vol in self.trade_history if side == "buy")
        sell_volume = sum(vol for ts, side, vol in self.trade_history if side == "sell")
        cumulative_delta = buy_volume - sell_volume
        
        # Объем за последнюю минуту (абсолютный)
        recent_trades = [t for t in self.trade_history if t[0] > current_time - 60]
        volume_per_minute = sum(abs(vol) for ts, side, vol in recent_trades)
        
        # Тренд имбаланса
        trend = self._calculate_trend(current_imbalance)
            
        # Обновление цены
        if bids and asks:
            self._update_price(bids, asks)

        # Логирование для отладки
        if len(self.trade_history) > 1000:
            logger.info(f"Trade history size: {len(self.trade_history)}")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "order_book_imbalance": round(current_imbalance, 4),
            "imbalance_trend": trend,
            "cumulative_delta": round(cumulative_delta, 2),
            "delta_per_minute": round(volume_per_minute, 2),
            "current_price": round(self.last_price, 2),
            "trade_count": len(self.trade_history),
            "valid_trades_processed": valid_trades_count
        }

feature_engine = FeatureEngine()