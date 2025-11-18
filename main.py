import time
from data_collector import LiveDataCollector
from feature_engine import feature_engine
from simple_strategy import SimpleStrategy
from telegram_notifier import telegram
from config import BUCKET_SECONDS

def run_bot():
    print("Bot starting...")
    telegram.send_bot_status("INFO BOT STARTED")

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
            
            # Вывод в консоль
            print(f"Price: {features['current_price']}")
            print(f"Delta: {features['delta']:.1f}")
            print(f"Abs UP: {features['absorption_up']}, DOWN: {features['absorption_down']}")
            print("---")

            # Отправляем ВСЕГДА данные в Telegram
            telegram_msg = f"Delta: {features['delta']:.1f} | UP: {features['absorption_up']} | DOWN: {features['absorption_down']}"
            telegram.send_trade_signal("info", telegram_msg)  # Используем side="info" для данных

            result = strat.analyze(features)

            if result["action"] == "SIGNAL":
                # Только выводим в консоль, в Telegram не отправляем сигналы
                print(f"SIGNAL: {result['side']} {result['price']:.2f} | {result['reason']}")
            else:
                print(f"HOLD | {result['reason']}")
            print("---")

            time.sleep(BUCKET_SECONDS)

    except KeyboardInterrupt:
        print("Bot stopped")
        telegram.send_bot_status("INFO BOT STOPPED")

if __name__ == "__main__":
    run_bot()