# simple_strategy.py
import time
from config import IMBALANCE_THRESHOLD, DELTA_THRESHOLD, MIN_VOLUME, CONFIRMATION_PERIODS

class SimpleStrategy:
    def __init__(self):
        self.open_position = None
        self.signal_confirmation = []  # Для подтверждения сигналов
        self.last_signal = None
    
    def analyze(self, features):
        imb = features.get("order_book_imbalance", 0.5)
        delta_value = features.get("cumulative_delta", 0.0)
        delta_per_minute = features.get("delta_per_minute", 0.0)
        trend = features.get("imbalance_trend", "flat")
        price = features.get("current_price", 0.0)

        # Фильтр по объему
        if abs(delta_per_minute) < MIN_VOLUME:
            return {"action": "HOLD", "reason": "low_volume"}

        signal = None
        
        # SHORT сигнал
        if (imb < (1 - IMBALANCE_THRESHOLD) and 
            delta_value < -DELTA_THRESHOLD and 
            trend == "falling"):
            signal = "SHORT"
        
        # LONG сигнал  
        elif (imb > IMBALANCE_THRESHOLD and 
              delta_value > DELTA_THRESHOLD and 
              trend == "rising"):
            signal = "LONG"

        # Подтверждение сигнала
        if signal:
            self.signal_confirmation.append(signal)
            # Оставляем только последние N сигналов
            self.signal_confirmation = self.signal_confirmation[-CONFIRMATION_PERIODS:]
            
            # Если все последние сигналы одинаковые - подтвержденный сигнал
            if (len(self.signal_confirmation) >= CONFIRMATION_PERIODS and 
                all(s == signal for s in self.signal_confirmation)):
                
                if self.open_position is None:
                    return {
                        "action": "ENTER",
                        "side": signal,
                        "price": price,
                        "reason": f"confirmed_{signal.lower()}_signal"
                    }
        else:
            # Сбрасываем подтверждение если нет сигнала
            self.signal_confirmation = []

        return {"action": "HOLD", "reason": "no_signal"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }
        # Сбрасываем подтверждение после входа
        self.signal_confirmation = []