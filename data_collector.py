# data_collector.py
# Simple collector: demo synthetic generator OR placeholder for live websocket
import threading
import time
import random
from datetime import datetime
from config import MODE, DEMO_PRICE, DEMO_VOL

class DataCollector:
    def __init__(self):
        self.order_book = None
        self.trades = []
        self.lock = threading.Lock()
        self.running = False
        self._thread = None
        self._price = DEMO_PRICE

    def start(self):
        if self.running:
            return
        self.running = True
        if MODE == "demo":
            self._thread = threading.Thread(target=self._demo_loop, daemon=True)
            self._thread.start()
        else:
            # For live/sandbox - user should implement OKX websocket here.
            self._thread = threading.Thread(target=self._live_stub_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _demo_loop(self):
        """Generate synthetic orderbook and trades rapidly; feature engine will aggregate to bucket."""
        while self.running:
            # small random walk
            self._price += random.gauss(0, DEMO_VOL)
            mid = max(1.0, self._price)

            # simple top-5 book
            bids = []
            asks = []
            for i in range(5):
                bids.append([round(mid - 0.5 - i*0.1 + random.uniform(-0.02,0.02), 2),
                             round(random.uniform(0.1, 5.0), 4)])
            for i in range(5):
                asks.append([round(mid + 0.5 + i*0.1 + random.uniform(-0.02,0.02), 2),
                             round(random.uniform(0.1, 5.0), 4)])

            trades = []
            for _ in range(random.randint(0,3)):
                side = random.choice(["buy","sell"])
                sz = round(random.expovariate(1.0),4)
                trade_price = round(mid + random.uniform(-0.5,0.5), 2)
                trades.append({"side": side, "sz": str(sz), "price": str(trade_price), "ts": datetime.utcnow().isoformat()})

            with self.lock:
                self.order_book = {"bids": bids, "asks": asks, "ts": datetime.utcnow().isoformat()}
                self.trades = trades

            time.sleep(0.25)

    def _live_stub_loop(self):
        """Placeholder — implement real websocket connection to OKX here."""
        while self.running:
            with self.lock:
                self.order_book = None
                self.trades = []
            time.sleep(1.0)

    def get_snapshot(self):
        with self.lock:
            ob = self.order_book
            trades = list(self.trades)
        return {"order_book": ob, "trades": trades}

# global instance
collector = DataCollector()
