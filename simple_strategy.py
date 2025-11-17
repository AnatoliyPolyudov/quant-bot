import time

class SimpleStrategy:
    """
    Тестовая версия стратегии как класс (совместим с main.py).
    ❌ НЕТ min hold
    ❌ НЕТ max hold
    ✅ Вход только по сильному сигналу
    ✅ Выход только по изменению сигнала (реверсу)
    """

    def __init__(self):
        self.open_position = None  # {"side","entry_ts","entry_price","entry_size"}
        self.last_trade_time = 0

        # Параметры (можно подправить в коде)
        self.IMB_THR = 0.35
        self.DELTA_THR = 8.0
        self.EXIT_IMB_THR = 0.20
        self.EXIT_DELTA_RATE_THR = 0.5

    def can_trade_now(self):
        # при необходимости можно добавить cool-down
        return True

    def analyze(self, features):
        """
        Вход: features - словарь из feature_engine.update_from_snapshot()
        Возвращает dict с ключами:
          - action: ENTER / EXIT / HOLD
          - side: LONG / SHORT (для ENTER)
          - reason: строка
        """
        # Поддерживаем обратную совместимость с разными названиями полей
        # (твой feature_engine использует order_book_imbalance, cumulative_delta, delta_per_minute, imbalance_trend)
        imb = features.get("order_book_imbalance") or features.get("imbalance") or 0.5
        delta_value = features.get("cumulative_delta") or features.get("delta") or 0.0
        delta_rate = features.get("delta_per_minute") or features.get("delta_rate") or 0.0
        trend = features.get("imbalance_trend") or features.get("trend") or "flat"
        price = features.get("current_price") or features.get("price") or 0.0

        pos = self.open_position

        # NO POSITION -> ищем вход
        if pos is None:
            # SHORT ENTRY
            if (
                imb < (1 - self.IMB_THR) and
                delta_value < -self.DELTA_THR and
                trend == "falling" and
                self.can_trade_now()
            ):
                return {
                    "action": "ENTER",
                    "side": "SHORT",
                    "price": price,
                    "reason": f"strong_short_imb_{imb:.4f}_delta_{delta_value:.2f}"
                }

            # LONG ENTRY
            if (
                imb > self.IMB_THR and
                delta_value > self.DELTA_THR and
                trend == "rising" and
                self.can_trade_now()
            ):
                return {
                    "action": "ENTER",
                    "side": "LONG",
                    "price": price,
                    "reason": f"strong_long_imb_{imb:.4f}_delta_{delta_value:.2f}"
                }

            return {"action": "HOLD", "reason": "no_signal"}

        # HAVE POSITION -> ищем выход (только по реальному реверсу)
        side = pos.get("side")

        # EXIT SHORT: покупатели растут + delta/min разворачивается вверх
        if side == "SHORT":
            if (
                imb > self.EXIT_IMB_THR and
                delta_rate > self.EXIT_DELTA_RATE_THR
            ):
                return {
                    "action": "EXIT",
                    "side": "SHORT",
                    "price": price,
                    "reason": f"short_reversal_imb_{imb:.3f}_drate_{delta_rate:.2f}"
                }

        # EXIT LONG: продавцы растут + delta/min разворачивается вниз
        if side == "LONG":
            if (
                imb < (1 - self.EXIT_IMB_THR) and
                delta_rate < -self.EXIT_DELTA_RATE_THR
            ):
                return {
                    "action": "EXIT",
                    "side": "LONG",
                    "price": price,
                    "reason": f"long_reversal_imb_{imb:.3f}_drate_{delta_rate:.2f}"
                }

        return {"action": "HOLD", "reason": "position_open"}

    def record_entry(self, side, price, size=None):
        self.open_position = {
            "side": side,
            "entry_ts": time.time(),
            "entry_price": price,
            "entry_size": size
        }
        self.last_trade_time = time.time()

    def record_exit(self):
        self.open_position = None
        self.last_trade_time = time.time()
