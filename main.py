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

    time.sleep(5)
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
                telegram.send_trade_signal(side, price)
                print(f"Signal: {side} at price {price:.2f}")

            time.sleep(BUCKET_SECONDS)

    except KeyboardInterrupt:
        print("Bot stopped")
        telegram.send_bot_status("stop")

if __name__ == "__main__":
    run_bot()
