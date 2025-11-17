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
                print("WebSocket not connected")
                time.sleep(1)
                continue

            features = feature_engine.update_from_snapshot(snapshot)
            
            # ОБНОВЛЕННАЯ печать - только то что есть
            print(f"Price: {features['current_price']}")
            print(f"Imbalance: {features['order_book_imbalance']:.3f}")
            print(f"Spoofing: {features['spoofing_flag']}")
            print(f"Volume: {features['recent_volume']:.1f}")
            print("---")

            result = strat.analyze(features)

            if result["action"] == "ENTER":
                side = result["side"]
                price = result["price"]
                strat.record_entry(side, price)
                telegram.send_trade_signal(side, price)
                print(f"SIGNAL: {side} {price:.2f}")
                print("===")
            else:
                print(f"HOLD: {result['reason']}")
                print("---")

            time.sleep(BUCKET_SECONDS)

    except KeyboardInterrupt:
        print("Bot stopped")
        telegram.send_bot_status("stop")

if __name__ == "__main__":
    run_bot()