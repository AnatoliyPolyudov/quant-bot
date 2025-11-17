import time

class SimpleStrategy:
    """
    Упрощенная стратегия: вход и выход по противоположным сигналам
    """

    def __init__(self):
        self.open_position = None  # {"side","entry_price","entry_ts","entry_size"}
        self.last_trade_time = 0

        # Единые пороги для входа и выхода
        self.IMB_THR = 0.35
        self.DELTA_THR = 8.0

    def analyze(self, features):
        """ Возвращает: {action, side?, price, reason} """
        imb = features.get("order_book_imbalance", 0.5)
        delta_value = features.get("cumulative_delta", 0.0)
        delta_rate = features.get("delta_per_minute", 0.0)
        trend = features.get("imbalance_trend", "flat")
        price = features.get("current_price", 0.0)

        pos = self.open_position

        # ==========================
        # ВХОД
        # ==========================
        if pos is None:
            # --- SHORT ---
            if (
                imb < (1 - self.IMB_THR) and
                delta_value < -self.DELTA_THR and
                trend == "falling"
            ):
                return {
                    "action": "ENTER",
                    "side": "SHORT",
                    "price": price,
                    "reason": f"strong_short_imb_{imb:.4f}_delta_{delta_value:.2f}"
                }

            # --- LONG ---
            if (
                imb > self.IMB_THR and
                delta_value > self.DELTA_THR and
                trend == "rising"
            ):
                return {
                    "action": "ENTER",
                    "side": "LONG",
                    "price": price,
                    "reason": f"strong_long_imb_{imb:.4f}_delta_{delta_value:.2f}"
                }

            return {"action": "HOLD", "reason": "no_signal"}

        # ==========================
        # ВЫХОД по противоположному сигналу
        # ==========================
        side = pos["side"]

        # --- EXIT SHORT при LONG сигнале ---
        if side == "SHORT":
            if (
                imb > self.IMB_THR and           # Имбаланс для LONG
                delta_value > self.DELTA_THR and # Дельта для LONG  
                trend == "rising"                # Тренд растущий
            ):
                return {
                    "action": "EXIT",
                    "price": price,
                    "side": "SHORT",
                    "reason": f"opposite_long_signal_imb_{imb:.4f}_delta_{delta_value:.2f}"
                }

        # --- EXIT LONG при SHORT сигнале ---
        if side == "LONG":
            if (
                imb < (1 - self.IMB_THR) and     # Имбаланс для SHORT
                delta_value < -self.DELTA_THR and # Дельта для SHORT
                trend == "falling"               # Тренд падающий
            ):
                return {
                    "action": "EXIT",
                    "price": price,
                    "side": "LONG", 
                    "reason": f"opposite_short_signal_imb_{imb:.4f}_delta_{delta_value:.2f}"
                }

        return {"action": "HOLD", "reason": "position_holding"}

    # ==========================
    # Запись позиции
    # ==========================

    def record_entry(self, side, price, size=None):
        self.open_position = {
            "side": side,
            "entry_price": price,
            "entry_ts": time.time(),
            "entry_size": size
        }
        self.last_trade_time = time.time()

    def record_exit(self):
        self.open_position = None
        self.last_trade_time = time.time()