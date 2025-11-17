import time
from data_collector import LiveDataCollector
from feature_engine import feature_engine
from simple_strategy import SimpleStrategy
from telegram_notifier import telegram
from config import BUCKET_SECONDS

def run_bot():
    print("Bot starting...")
    telegram.send_bot_status("start")

    collector = LiveDataCollector()
    strat = SimpleStrategy()

    time.sleep(5)  # дать время на подключение WS
    print("Bot is running...")

    try:
        while True:
            snapshot = collector.get_snapshot()
            if not snapshot.get("connected", False):
                time.sleep(1)
                continue

            features = feature_engine.update_from_snapshot(snapshot)

            result = strat.analyze(features)
            if result["action"] == "ENTER":
                side = result["side"]
                price = result["price"]
                strat.record_entry(side, price)

                # Минималистичное уведомление
                telegram.send_trade_signal(
                    action="ENTER",
                    side=side,
                    price=price,
                    size=0,  # не учитываем размер
                    reason=result.get("reason", ""),
                    metrics={
                        "imbalance": features.get("order_book_imbalance", 0),
                        "delta": features.get("cumulative_delta", 0),
                        "trend": features.get("imbalance_trend", "N/A"),
                        "delta_per_minute": features.get("delta_per_minute", 0)
                    }
                )
                print(f"Signal: {side} at price {price:.2f}")

            time.sleep(BUCKET_SECONDS)

    except KeyboardInterrupt:
        print("Bot stopped")
        telegram.send_bot_status("stop")


if __name__ == "__main__":
    run_bot()
