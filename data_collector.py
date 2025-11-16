# data_collector.py - ТОЛЬКО LIVE OKX
import json
import threading
import websocket
import time
from datetime import datetime
from config import SYMBOL

class LiveDataCollector:
    def __init__(self):
        self.price = None
        self.best_bid = None
        self.best_ask = None
        self.spread = None
        self.bids = []
        self.asks = []
        self.trades = []
        
        self.lock = threading.Lock()
        self._ws = None
        self.connected = False

        print("[Collector] Starting OKX WebSocket connection...")
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

        # Запускаем в отдельном потоке
        self.ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True)
        self.ws_thread.start()

    def _on_open(self, ws):
        print("[Collector] ✅ Connected to OKX WebSocket")
        self.connected = True
        
        # Подписываемся на стакан и трейды
        sub_msg = {
            "op": "subscribe",
            "args": [
                {"channel": "books5", "instId": SYMBOL},
                {"channel": "trades", "instId": SYMBOL}
            ]
        }
        ws.send(json.dumps(sub_msg))
        print("[Collector] ✅ Subscribed to books5 & trades")

    def _on_error(self, ws, error):
        print(f"[Collector] ❌ WebSocket error: {error}")
        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        print(f"[Collector] 🔌 WebSocket closed: {close_status_code} - {close_msg}")
        self.connected = False

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
            
            if "event" in msg:
                if msg["event"] == "subscribe":
                    print(f"[Collector] ✅ Subscribed to: {msg.get('arg', {})}")
                return

            if "arg" not in msg:
                return

            channel = msg["arg"]["channel"]

            with self.lock:
                if channel == "books5" and "data" in msg:
                    self._handle_books(msg["data"][0])
                elif channel == "trades" and "data" in msg:
                    self._handle_trades(msg["data"])
                    
        except Exception as e:
            print(f"[Collector] ❌ Message processing error: {e}")

    def _handle_books(self, book_data):
        """Обрабатываем стакан"""
        try:
            self.bids = book_data.get("bids", [])
            self.asks = book_data.get("asks", [])
            
            if self.bids and self.asks:
                self.best_bid = float(self.bids[0][0])
                self.best_ask = float(self.asks[0][0])
                self.price = (self.best_bid + self.best_ask) / 2
                self.spread = self.best_ask - self.best_bid
                
        except Exception as e:
            print(f"[Collector] ❌ Book processing error: {e}")

    def _handle_trades(self, trades_data):
        """Обрабатываем трейды"""
        try:
            self.trades = trades_data[-10:]  # Берем последние 10 трейдов
        except Exception as e:
            print(f"[Collector] ❌ Trade processing error: {e}")

    def get_snapshot(self):
        """Возвращает текущий снапшот данных"""
        with self.lock:
            return {
                "order_book": {
                    "bids": self.bids,
                    "asks": self.asks,
                    "ts": datetime.utcnow().isoformat()
                },
                "trades": self.trades,
                "price": self.price,
                "spread": self.spread,
                "connected": self.connected
            }

    def stop(self):
        """Останавливает соединение"""
        if self._ws:
            self._ws.close()
        self.connected = False
