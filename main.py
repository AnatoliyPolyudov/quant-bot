import time
from data_collector import LiveDataCollector
from feature_engine import FeatureEngine
from simple_strategy import SimpleStrategy
from live_executor import LiveExecutor
from telegram_notifier import telegram
from config import BUCKET_SECONDS, POSITION_PCT


def calc_pnl(entry_price, exit_price, size, side):
    """Возвращает (pnl_usd, pnl_pct)."""
    if side == "LONG":
        pnl_usd = (exit_price - entry_price) * size
    else:  # SHORT
        pnl_usd = (entry_price - exit_price) * size
    
    pnl_pct = (exit_price / entry_price - 1) * (1 if side == "LONG" else -1)
    return pnl_usd, pnl_pct


def run_bot():
    print(f"🚀 Starting Quantum Bot LITE v1.1")
    
    try: telegram.send_bot_status("STARTING", "1.1")
    except: pass

    collector = LiveDataCollector()
    fe = FeatureEngine()
    strat = SimpleStrategy()
    executor = LiveExecutor(dry_run=True)  # DRY-RUN FOR SAFETY

    last_bucket = 0
    time.sleep(5)

    try:
        telegram.send_bot_status("RUNNING", "1.1")
    except: pass

    while True:
        now = time.time()
        if now - last_bucket >= BUCKET_SECONDS:
            snapshot = collector.get_snapshot()
            if not snapshot.get("connected", False):
                print("❌ WebSocket not ready")
                time.sleep(1)
                continue

            features = fe.update_from_snapshot(snapshot)
            last_bucket = now

            # Лог статуса
            print("="*60)
            print(f"📊 {features['timestamp'][11:19]} Price: ${features['current_price']:.2f}")
            print(f"📈 I: {features['order_book_imbalance']:.3f}  Trend: {features['imbalance_trend']}")
            print(f"Δ: {features['cumulative_delta']:.1f} ({features['delta_per_minute']:.1f}/m)")
            print(f"Spread: {features['spread_percent']:.4f}%")

            # --- STRATEGY ---
            result = strat.analyze(features)
            print(f"🤖 Strategy: {result['action']} {result.get('reason', '')}")

            # ========= ENTER =========
            if result["action"] == "ENTER":
                side = result["side"]
                entry_price = result["price"]

                order = executor.safe_enter_from_equity_pct(side, POSITION_PCT)

                size = order.get("size") if order else 0
                strat.record_entry(side, entry_price, size)

                # Telegram
                try:
                    telegram.send_trade_executed(
                        action="ENTER",
                        side=side,
                        price=entry_price,
                        size=size,
                        notional=order.get("notional", 0),
                        order_id=(
                            order.get("resp", {}).get("data", [{}])[0].get("ordId")
                            if order and order.get("resp") else "SIMULATED"
                        )
                    )
                except:
                    pass

            # ========= EXIT =========
            elif result["action"] == "EXIT" and strat.open_position:

                pos = strat.open_position
                exit_price = result.get("price") or features["current_price"]

                # Execute exit
                exit_order = executor.exit_position_market()

                # Calculate PnL
                pnl_usd, pnl_pct = calc_pnl(
                    entry_price=pos["entry_price"],
                    exit_price=exit_price,
                    size=pos["entry_size"] or 0,
                    side=pos["side"]
                )

                hold_minutes = (time.time() - pos["entry_ts"]) / 60

                # FULL REPORT
                report = (
                    f"📉 EXIT {pos['side']}\n"
                    f"Entry: ${pos['entry_price']:.2f}\n"
                    f"Exit:  ${exit_price:.2f}\n"
                    f"PnL: {pnl_pct*100:.3f}%  (${pnl_usd:.4f})\n"
                    f"Hold: {hold_minutes:.1f}m\n"
                    f"Reason: {result.get('reason', '-')}"
                )

                print("\n" + report + "\n")

                # Telegram
                try:
                    telegram.send_message(report)
                except:
                    pass

                strat.record_exit()

        time.sleep(0.05)
