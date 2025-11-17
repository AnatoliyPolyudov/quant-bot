# main.py - С TELEGRAM УВЕДОМЛЕНИЯМИ (под SimpleStrategy)
import time
from data_collector import LiveDataCollector
from feature_engine import FeatureEngine
from simple_strategy import SimpleStrategy
from live_executor import LiveExecutor
from telegram_notifier import telegram
from config import MODE, BUCKET_SECONDS, POSITION_PCT, IMBALANCE_THRESHOLD, DELTA_THRESHOLD


def run_bot():
    print(f"🚀 Starting Quantum Bot LITE v1.0 - LIVE MODE")
    
    # Отправляем статус в Telegram (если telegram настроен)
    try:
        telegram.send_bot_status("STARTING", "1.0")
    except Exception:
        pass

    print(f"📈 Symbol: BTC-USDT-SWAP")
    print(f"⏰ Timeframe: 1-MINUTE ANALYSIS") 
    print(f"💰 Equity: $100, Position: {POSITION_PCT*100}%")
    print(f"⚡ Strategy: imb>{IMBALANCE_THRESHOLD}, delta>{DELTA_THRESHOLD}")

    # Инициализация модулей
    collector = LiveDataCollector()
    fe = FeatureEngine()
    strat = SimpleStrategy()
    executor = LiveExecutor(dry_run=True)  # ДЛЯ ТЕСТОВ ДЕРЖИМ DRY_RUN=True по умолчанию

    last_bucket = 0
    startup_delay = 5  # Ждем подключения к WebSocket

    print(f"⏳ Waiting {startup_delay}s for WebSocket connection...")
    time.sleep(startup_delay)

    try:
        # Отправляем статус что бот запущен
        try:
            telegram.send_bot_status("RUNNING", "1.0")
        except Exception:
            pass
        
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
                    side = result.get("side")
                    print(f"💰 ENTER {side} SIGNAL! reason={result.get('reason')}")
                    notional_pct = POSITION_PCT
                    order_result = executor.safe_enter_from_equity_pct(side, notional_pct)

                    # order_result может быть None или dict
                    if order_result:
                        # order_result обычно содержит price, size, resp, notional
                        entry_price = order_result.get("price") or result.get("price") or features.get("current_price")
                        entry_size = order_result.get("size") or result.get("size")
                        notional = order_result.get("notional")
                    else:
                        entry_price = result.get("price") or features.get("current_price")
                        entry_size = result.get("size")
                        notional = None

                    # Telegram уведомление (без падения при ошибке)
                    try:
                        telegram.send_trade_executed(
                            action="ENTER",
                            side=side,
                            price=entry_price,
                            size=entry_size or 0,
                            notional=notional or 0,
                            order_id=(order_result.get("resp", {}).get("data", [{}])[0].get("ordId") if order_result and order_result.get("resp") else "SIMULATED")
                        )
                    except Exception:
                        pass

                    strat.record_entry(side, entry_price, entry_size)

                elif result["action"] == "EXIT":
                    print(f"💰 EXIT SIGNAL! reason={result.get('reason')}")
                    exit_result = executor.exit_position_market()
                    try:
                        telegram.send_trade_executed(
                            action="EXIT",
                            side=result.get("side") or (strat.open_position.get("side") if strat.open_position else "UNKNOWN"),
                            price=features.get("current_price"),
                            size=(strat.open_position.get("entry_size") if strat.open_position else 0),
                            notional=0,
                            order_id=(exit_result.get("resp", {}).get("data", [{}])[0].get("ordId") if exit_result and exit_result.get("resp") else "SIMULATED")
                        )
                    except Exception:
                        pass

                    strat.record_exit()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        try:
            telegram.send_bot_status("STOPPED", "1.0")
        except Exception:
            pass
    except Exception as e:
        error_msg = f"Critical error: {e}"
        print(f"\n❌ {error_msg}")
        try:
            telegram.send_error(error_msg)
        except Exception:
            pass
        import traceback
        traceback.print_exc()
    finally:
        collector.stop()
        try:
            telegram.send_bot_status("SHUTDOWN", "1.0")
        except Exception:
            pass
        print("✅ Bot shutdown complete")


if __name__ == '__main__':
    run_bot()
