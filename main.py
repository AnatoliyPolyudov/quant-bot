# main.py
import time
from data_collector import collector
from feature_engine import feature_engine
from simple_strategy import SimpleStrategy
from live_executor import LiveExecutor
from config import MODE, BUCKET_SECONDS, POSITION_PCT

def run_bot(runtime_seconds=300):
    print("Starting Quantum Bot LITE v1.0 (MODE=%s)" % MODE)
    collector.start()
    strat = SimpleStrategy()
    execer = LiveExecutor(dry_run=True)  # start in dry-run; set to False only after sandbox tests

    start = time.time()
    last_feature_time = 0
    try:
        while True:
            now = time.time()
            snapshot = collector.get_snapshot()
            if now - last_feature_time >= BUCKET_SECONDS:
                features = feature_engine.update_from_snapshot(snapshot)
                last_feature_time = now

                result = strat.analyze(features)

                # Print basic diagnostics
                print("----", features['timestamp'], "price:", features['current_price'])
                print("imbalance:", features['order_book_imbalance'], "delta:", features['cumulative_delta'], "spread%:", features['spread_percent'])
                print("Strategy:", result)

                if result['action'] == "ENTER":
                    # compute notional from fraction POSITION_PCT (e.g., 0.05 = 5% of equity)
                    notional_pct = POSITION_PCT
                    if notional_pct > 1:
                        notional_pct = notional_pct / 100.0
                    # use safe_enter
                    resp = execer.safe_enter_from_equity_pct(result['side'], notional_pct)
                    strat.record_entry(result['side'], result.get('price', features['current_price']))

                if result['action'] == "EXIT":
                    resp = execer.exit_position_market()
                    strat.record_exit()

            if runtime_seconds and (now - start) > runtime_seconds:
                print("Run time elapsed, stopping...")
                break

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        collector.stop()

if __name__ == '__main__':
    run_bot(runtime_seconds=600)
