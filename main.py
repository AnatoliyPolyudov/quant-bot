# main.py - FIXED FOR LIVE ONLY
import time
from data_collector import LiveDataCollector
from feature_engine import FeatureEngine
from simple_strategy import SimpleStrategy
from live_executor import LiveExecutor
from config import MODE, BUCKET_SECONDS, POSITION_PCT


def run_bot():
    print(f"🚀 Starting Quantum Bot LITE v1.0 - LIVE MODE")
    print(f"📈 Symbol: BTC-USDT-SWAP")
    print(f"💰 Equity: $100, Position: {POSITION_PCT*100}%")
    print(f"⚡ Strategy: imb>{IMBALANCE_THRESHOLD}, delta>{DELTA_THRESHOLD}")

    # Инициализация модулей
    collector = LiveDataCollector()
    fe = FeatureEngine()
    strat = SimpleStrategy()
    executor = LiveExecutor(dry_run=False)  # LIVE TRADING!

    last_bucket = 0
    startup_delay = 5  # Ждем подключения к WebSocket

    print(f"⏳ Waiting {startup_delay}s for WebSocket connection...")
    time.sleep(startup_delay)

    try:
        while True:
            now = time.time()

            # Обрабатываем данные каждую секунду
            if now - last_bucket >= BUCKET_SECONDS:
                snapshot = collector.get_snapshot()
                
                if not snapshot.get("connected", False):
                    print("❌ WebSocket not connected, retrying...")
                    time.sleep(1)
                    continue

                features = fe.update_from_snapshot(snapshot)
                last_bucket = now

                # Выводим статус
                print("\n" + "="*60)
                print(f"📊 {features['timestamp'][11:19]} | Price: ${features['current_price']:.2f}")
                print(f"📈 Imbalance: {features['order_book_imbalance']:.3f} | Delta: {features['cumulative_delta']:.1f}")
                print(f"📏 Spread: {features['spread_percent']:.4f}%")
                
                # Анализ стратегии
                result = strat.analyze(features)
                print(f"🤖 Strategy: {result['action']} - {result.get('reason', '')}")

                # Исполнение
                if result["action"] == "ENTER":
                    print(f"💰 ENTER {result['side']} SIGNAL!")
                    notional_pct = POSITION_PCT
                    executor.safe_enter_from_equity_pct(result["side"], notional_pct)
                    strat.record_entry(result["side"], features["current_price"])

                elif result["action"] == "EXIT":
                    print(f"💰 EXIT SIGNAL!")
                    executor.exit_position_market()
                    strat.record_exit()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
    finally:
        collector.stop()
        print("✅ Bot shutdown complete")


if __name__ == '__main__':
    run_bot()
