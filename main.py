# main.py - С TELEGRAM УВЕДОМЛЕНИЯМИ
import time
from data_collector import LiveDataCollector
from feature_engine import FeatureEngine
from simple_strategy import SimpleStrategy
from live_executor import LiveExecutor
from telegram_notifier import telegram
from config import MODE, BUCKET_SECONDS, POSITION_PCT, IMBALANCE_THRESHOLD, DELTA_THRESHOLD


def run_bot():
    print(f"🚀 Starting Quantum Bot LITE v1.0 - LIVE MODE")
    
    # Отправляем статус в Telegram
    telegram.send_bot_status("STARTING", "1.0")

    print(f"📈 Symbol: BTC-USDT-SWAP")
    print(f"⏰ Timeframe: 1-MINUTE ANALYSIS") 
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
        # Отправляем статус что бот запущен
        telegram.send_bot_status("RUNNING", "1.0")
        
        while True:
            now = time.time()

            # Обрабатываем данные КАЖДУЮ МИНУТУ
            if now - last_bucket >= BUCKET_SECONDS:
                snapshot = collector.get_snapshot()
                
                if not snapshot.get("connected", False):
                    print("❌ WebSocket not connected, retrying...")
                    time.sleep(1)
                    continue

                features = fe.update_from_snapshot(snapshot)
                last_bucket = now

                # Выводим статус С ОБНОВЛЕННЫМИ МЕТРИКАМИ
                print("\n" + "="*60)
                print(f"📊 {features['timestamp'][11:19]} | Price: ${features['current_price']:.2f}")
                print(f"📈 Imbalance: {features['order_book_imbalance']:.3f} | Trend: {features['imbalance_trend']}")
                print(f"📊 Delta: {features['cumulative_delta']:.1f} ({features['delta_per_minute']:.1f}/min)")
                print(f"🎯 Spread: {features['spread_percent']:.4f}%")
                
                # Анализ стратегии
                result = strat.analyze(features)
                print(f"🤖 Strategy: {result['action']} - {result.get('reason', '')}")

                # Исполнение
                if result["action"] == "ENTER":
                    print(f"💰 ENTER {result['side']} SIGNAL!")
                    notional_pct = POSITION_PCT
                    order_result = executor.safe_enter_from_equity_pct(result["side"], notional_pct)
                    
                    # Отправляем уведомление о исполнении
                    if order_result:
                        telegram.send_trade_executed(
                            action="ENTER",
                            side=result["side"],
                            price=result["price"],
                            size=result.get("size", 0),
                            notional=result.get("notional", 0),
                            order_id=order_result.get("resp", {}).get("data", [{}])[0].get("ordId") if order_result.get("resp") else "SIMULATED"
                        )
                    
                    strat.record_entry(result["side"], result["price"], result.get("size"))

                elif result["action"] == "EXIT":
                    print(f"💰 EXIT SIGNAL!")
                    exit_result = executor.exit_position_market()
                    strat.record_exit()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        telegram.send_bot_status("STOPPED", "1.0")
    except Exception as e:
        error_msg = f"Critical error: {e}"
        print(f"\n❌ {error_msg}")
        telegram.send_error(error_msg)
        import traceback
        traceback.print_exc()
    finally:
        collector.stop()
        telegram.send_bot_status("SHUTDOWN", "1.0")
        print("✅ Bot shutdown complete")


if __name__ == '__main__':
    run_bot()
