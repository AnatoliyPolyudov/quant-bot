# simple_strategy.py
import time

class SimpleStrategy:
    def __init__(self):
        self.open_position = None
        self.last_signal_time = 0
        self.signal_cooldown = 300  # 5 минут коoldown между сигналами

    def analyze(self, features):
        price = features.get("current_price", 0.0)
        delta = features.get("delta", 0)
        abs_up = features.get("absorption_up", False)
        abs_down = features.get("absorption_down", False)
        current_time = time.time()

        # 🔒 Игнорируем если позиция открыта
        if self.open_position is not None:
            return {"action": "HOLD", "reason": "position_open"}

        # ⏳ Игнорируем если не прошел коoldown
        if current_time - self.last_signal_time < self.signal_cooldown:
            return {"action": "HOLD", "reason": "cooldown"}

        # 🎯 LONG сигнал - ВЫШЕ порог для надежности
        if delta < -1.0 or abs_down:  # УВЕЛИЧЕНО с -0.5 до -1.0
            self.last_signal_time = current_time
            return {
                "action": "ENTER",
                "side": "LONG", 
                "price": price,
                "reason": f"absorption_down / delta {delta:.1f}"
            }

        # 🎯 SHORT сигнал - ВЫШЕ порог для надежности  
        if delta > 1.0 or abs_up:  # УВЕЛИЧЕНО с 0.5 до 1.0
            self.last_signal_time = current_time
            return {
                "action": "ENTER",
                "side": "SHORT",
                "price": price,
                "reason": f"absorption_up / delta {delta:.1f}"
            }

        return {"action": "HOLD", "reason": f"no signal delta {delta:.1f}"}

    def record_entry(self, side, price):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time()
        }

    def close_position(self):
        """Закрыть позицию (для тестирования)"""
        self.open_position = None