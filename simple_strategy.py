import time

class SimpleStrategy:
    def __init__(self):
        # УБИРАЕМ открытую позицию - бот только информационный
        pass

    def analyze(self, features):
        price = features.get("current_price", 0.0)
        delta = features.get("delta", 0)
        abs_up = features.get("absorption_up", False)
        abs_down = features.get("absorption_down", False)

        # 🎯 LONG сигнал
        if delta < -1.0 or abs_down:
            return {
                "action": "SIGNAL",  # Меняем ENTER на SIGNAL
                "side": "LONG", 
                "price": price,
                "reason": f"LONG - absorption_down / delta {delta:.1f}"
            }

        # 🎯 SHORT сигнал  
        if delta > 1.0 or abs_up:
            return {
                "action": "SIGNAL",  # Меняем ENTER на SIGNAL
                "side": "SHORT",
                "price": price,
                "reason": f"SHORT - absorption_up / delta {delta:.1f}"
            }

        return {"action": "HOLD", "reason": f"delta {delta:.1f}"}