# data_collector.py
import websocket
import json
import threading
import time

class OKXDataCollector:
    def __init__(self):
        self.ws = None
        self.data_buffer = []
        
    def on_message(self, ws, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            print(f"📥 Received: {data.get('arg', {}).get('channel', 'unknown')}")
            
            # Сохраняем данные
            if 'data' in data:
                self.data_buffer.extend(data['data'])
                
        except Exception as e:
            print(f"❌ Message error: {e}")
    
    def on_error(self, ws, error):
        print(f"❌ WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 WebSocket closed")
    
    def on_open(self, ws):
        print("🔌 WebSocket connected")
        # Подписываемся на каналы
        from config import CHANNELS
        for channel in CHANNELS:
            subscribe_msg = {
                "op": "subscribe",
                "args": [{"channel": channel}]
            }
            ws.send(json.dumps(subscribe_msg))
            print(f"📡 Subscribed to: {channel}")
    
    def start(self):
        """Запуск сбора данных"""
        from config import WS_URL
        
        self.ws = websocket.WebSocketApp(
            WS_URL,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        
        # Запускаем в отдельном потоке
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        print("🚀 Data collector started")

# Глобальный экземпляр
data_collector = OKXDataCollector()
