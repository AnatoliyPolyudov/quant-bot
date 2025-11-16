# simple_strategy.py - УМНЫЕ ВЫХОДЫ БЕЗ ШУМА
import time
from config import (IMBALANCE_THRESHOLD, DELTA_THRESHOLD, SPREAD_MAX_PCT, 
                   MIN_SIGNAL_INTERVAL, TRADE_HOLD_SECONDS,
                   EXIT_IMBALANCE_THRESHOLD, EXIT_DELTA_PER_MINUTE, MIN_HOLD_SECONDS)

class SimpleStrategy:
    def __init__(self):
        self.last_trade_time = 0
        self.open_position = None  # {"side","entry_ts","entry_price"}

    def can_trade_now(self):
        return (time.time() - self.last_trade_time) >= MIN_SIGNAL_INTERVAL

    def analyze(self, features):
        imb = features.get("order_book_imbalance", 0.5)
        imb_trend = features.get("imbalance_trend", "flat")
        delta = features.get("cumulative_delta", 0.0)
        delta_rate = features.get("delta_per_minute", 0.0)
        spread = features.get("spread_percent", 999.0)
        price = features.get("current_price", 0.0)

        # Reject if spread large or malformed
        if spread <= 0 or spread > SPREAD_MAX_PCT:
            return {"action": "HOLD", "reason": "spread_bad", "confidence": 0}

        # Если есть открытая позиция - УМНАЯ ЛОГИКА ВЫХОДА
        if self.open_position:
            current_time = time.time()
            position_age = current_time - self.open_position["entry_ts"]
            
            # МИНИМАЛЬНОЕ ВРЕМЯ УДЕРЖАНИЯ - НЕ ВЫХОДИМ РАНЬШЕ 2 МИНУТ
            if position_age < MIN_HOLD_SECONDS:
                return {"action": "HOLD", "reason": "min_hold_time", "confidence": 0}
            
            # ВРЕМЕННОЙ ВЫХОД - после 5 минут
            if position_age >= TRADE_HOLD_SECONDS:
                return {"action": "EXIT", "reason": "time_exit", "side": self.open_position["side"], "price": price}
            
            # УМНЫЙ ВЫХОД ПО РАЗВОРОТУ - ТОЛЬКО ПРИ СИГНАЛАХ
            if self.open_position["side"] == "LONG":
                # Выход только при СИЛЬНОМ развороте
                if imb < EXIT_IMBALANCE_THRESHOLD and delta_rate < EXIT_DELTA_PER_MINUTE:
                    return {"action": "EXIT", "reason": "strong_reversal", "side": "LONG", "price": price}
                    
            elif self.open_position["side"] == "SHORT":
                # Выход только при СИЛЬНОМ развороте  
                if imb > (1.0 - EXIT_IMBALANCE_THRESHOLD) and delta_rate > -EXIT_DELTA_PER_MINUTE:
                    return {"action": "EXIT", "reason": "strong_reversal", "side": "SHORT", "price": price}
            
            return {"action": "HOLD", "reason": "position_open", "confidence": 0}

        # Нет открытой позиции - СТРОГИЕ УСЛОВИЯ ВХОДА
        # LONG: имбаланс > 0.70 И дельта > 8.0 И тренд растущий
        if (imb > IMBALANCE_THRESHOLD and 
            delta > DELTA_THRESHOLD and 
            imb_trend == "rising" and 
            self.can_trade_now()):
            
            return {
                "action": "ENTER", 
                "side": "LONG", 
                "price": price, 
                "confidence": 90, 
                "reason": f"strong_long_imb_{imb}_delta_{delta}"
            }
        
        # SHORT: имбаланс < 0.30 И дельта < -8.0 И тренд падающий  
        if (imb < (1.0 - IMBALANCE_THRESHOLD) and 
            delta < -DELTA_THRESHOLD and 
            imb_trend == "falling" and 
            self.can_trade_now()):
            
            return {
                "action": "ENTER", 
                "side": "SHORT", 
                "price": price, 
                "confidence": 90, 
                "reason": f"strong_short_imb_{imb}_delta_{delta}"
            }

        return {"action": "HOLD", "reason": "no_signal", "confidence": 0}

    def record_entry(self, side, price):
        self.open_position = {"side": side, "entry_ts": time.time(), "entry_price": price}
        self.last_trade_time = time.time()

    def record_exit(self):
        self.open_position = None
        self.last_trade_time = time.time()
