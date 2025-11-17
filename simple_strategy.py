import time

def simple_strategy(features, strat):
    """
    Тестовая версия стратегии:
    ❌ НЕТ min hold
    ❌ НЕТ max hold
    ✅ Вход только по сильному сигналу
    ✅ Выход только по изменению сигнала (реверсу)
    """

    imb = features["imbalance"]
    delta_value = features["delta"]
    delta_rate = features["delta_per_minute"]  # delta/min
    trend = features["trend"]

    # Порог для входа
    IMB_THR = 0.35
    DELTA_THR = 8.0

    # Порог для выхода — слабый реверс
    EXIT_IMB_THR = 0.20
    EXIT_DELTA_RATE_THR = 0.5

    pos = strat.open_position

    # =============================
    # NO POSITION → ищем вход
    # =============================
    if pos is None:

        # ---- SHORT ENTRY ----
        if (
            imb < (1 - IMB_THR) and
            delta_value < -DELTA_THR and
            trend == "falling"
        ):
            return {
                "action": "ENTER",
                "side": "SHORT",
                "reason": f"strong_short_imb_{imb:.4f}_delta_{delta_value:.2f}"
            }

        # ---- LONG ENTRY ----
        if (
            imb > IMB_THR and
            delta_value > DELTA_THR and
            trend == "rising"
        ):
            return {
                "action": "ENTER",
                "side": "LONG",
                "reason": f"strong_long_imb_{imb:.4f}_delta_{delta_value:.2f}"
            }

        return {"action": "HOLD"}

    # =============================
    # HAVE POSITION → ищем выход
    # =============================

    side = pos["side"]

    # ---- EXIT SHORT ----
    if side == "SHORT":
        if (
            imb > EXIT_IMB_THR and        # покупатели растут
            delta_rate > EXIT_DELTA_RATE_THR  # delta/min разворачивается вверх
        ):
            return {
                "action": "EXIT",
                "reason": f"short_reversal_imb_{imb:.3f}_drate_{delta_rate:.2f}"
            }

    # ---- EXIT LONG ----
    if side == "LONG":
        if (
            imb < (1 - EXIT_IMB_THR) and         # продавцы растут
            delta_rate < -EXIT_DELTA_RATE_THR    # delta/min вниз
        ):
            return {
                "action": "EXIT",
                "reason": f"long_reversal_imb_{imb:.3f}_drate_{delta_rate:.2f}"
            }

    # Если нет сигнала выхода — держим
    return {"action": "HOLD"}
