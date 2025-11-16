# main.py

import time
from data_collector import DataCollector
from feature_engine import FeatureEngine
from simple_strategy import SimpleStrategy
from live_executor import LiveExecutor
from config import MODE, BUCKET_SECONDS, POSITION_PCT


def run_bot(runtime_seconds=300):
    print(f"Starting Quantum Bot LITE v1.0 (MODE={MODE})")

    # 1. INIT MODULES
    collector = DataCollector()
    collector.start()

    strat = SimpleStrategy()
    executor = LiveExecutor(dry_run=(MODE != "LIVE"))  # If MODE=LIVE → real trading

    fe = FeatureEngine()

    start = time.time()
    last_bucket = 0

    try:
        while True:
            now = time.time()

            # 2. Process data every BUCKET_SECONDS seconds
            if now - last_bucket >= BUCKET_SECONDS:
                snapshot = collector.get_snapshot()
                features = fe.update_from_snapshot(snapshot)
                last_bucket = now

                # Diagnostics
                print("-----", features["timestamp"], "price:", features["current_price"])
                print("imb:", features["order_book_imbalance"],
                      "delta:", features["cumulative_delta"],
                      "spread:", features["spread_percent"])
                
                result = strat.analyze(features)
                print("Strategy:", result)

                # 3. EXECUTION
                if result["action"] == "ENTER":
                    notional_pct = POSITION_PCT / 100 if POSITION_PCT > 1 else POSITION_PCT
                    executor.safe_enter_from_equity_pct(result["side"], notional_pct)

                    strat.record_entry(result["side"], features["current_price"])

                elif result["action"] == "EXIT":
                    executor.exit_position_market()
                    strat.record_exit()

            # 4. Stop by timeout
            if runtime_seconds and (now - start) >= runtime_seconds:
                print("Runtime finished. Stopping bot...")
                break

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Interrupted manually")

    finally:
        collector.stop()
        print("Collector stopped. Clean exit.")


if __name__ == '__main__':
    run_bot(runtime_seconds=600)
