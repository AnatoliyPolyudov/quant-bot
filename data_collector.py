import json
import threading
import websocket
import time
from datetime import datetime
from config import SYMBOL, MODE

class LiveDataCollector:
    def __init__(self):
        self.price = None
        self.best_bid = None
        self.best_ask = None
        self.spread = None
        self.delta = 0
        self.last_buy_vol = 0
        self.last_sell_vol = 0
        self.trade_imbalance = 0

        self.trades_buffer = []
        self.lock = threading.Lock()

        self._ws = None

        print("[Collector] Initializing live mode...")
        self._start_ws()

    def _start_ws(self):
        url = "wss://ws.okx.com:8443/ws/v5/public"
        self._ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        t = threading.Thread(target=self._ws.run_forever, daemon=True)
        t.start()

    def _on_open(self, ws):
        print("[Collector] Connected to OKX WebSocket")

        sub_msg = {
            "op": "subscribe",
            "args": [
                {"channel": "books5", "instId": SYMBOL},
                {"channel": "trades", "instId": SYMBOL}
            ]
        }
        ws.send(json.dumps(sub_msg))
        print("[Collector] Subscribed to books5 & trades")

    def _on_error(self, ws, error):
        print("[Collector] ERROR:", error)

    def _on_close(self, ws, *args):
        print("[Collector] WebSocket closed")

    def _on_message(self, ws, message):
        msg = json.loads(message)

        if "arg" not in msg:
            return

        channel = msg["arg"]["channel"]

        if channel == "books5":
            self._handle_books(msg)

        elif channel == "trades":
            self._handle_trades(msg)

    def _handle_books(self, msg):
        if "data" not in msg:
            return

        data = msg["data"][0]

        bid = float(data["bids"][0][0])
        ask = float(data["asks"][0][0])

        with self.lock:
            self.best_bid = bid
            self.best_ask = ask
            self.price = (bid + ask) / 2
            self.spread = ask - bid

    def _handle_trades(self, msg):
        if "data" not in msg:
            return

        trades = msg["data"]

        with self.lock:
            for t in trades:
                px = float(t["px"])
                sz = float(t["sz"])
                side = t["side"]  # buy or sell

                if side == "buy":
                    self.last_buy_vol += sz
                else:
                    self.last_sell_vol += sz

            # Calculate imbalance
            total = self.last_buy_vol + self.last_sell_vol
            if total > 0:
                self.trade_imbalance = (self.last_buy_vol - self.last_sell_vol) / total

            # Reset every update to make it short-term impulse
            self.last_buy_vol = 0
            self.last_sell_vol = 0

    def get_snapshot(self):
        with self.lock:
            return {
                "price": self.price,
                "spread": self.spread,
                "imbalance": self.trade_imbalance,
                "ts": time.time()
            }
