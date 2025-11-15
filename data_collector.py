# data_collector.py
import websocket
import json
import threading
import time
from datetime import datetime
from feature_engine import feature_engine

class OKXDataCollector:
    def __init__(self):
        self.ws = None
        self.data_buffer = []
        self.message_count = 0
        self.last_feature_print = 0
        
        # Раздельные буферы для разных типов данных
        self.order_book_data = []
        self.trade_data = []
        self.ticker_data = []
        
    def on_message(self, ws, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            self.message_count += 1
            
            # Обрабатываем разные типы сообщений
            if 'event' in data:
                print(f"⚡ Event: {data['event']} - {data.get('msg', '')}")
            elif 'data' in data:
                channel = data.get('arg', {}).get('channel', 'unknown')
                print(f"📥 [{self.message_count}] {channel}: {len(data['data'])} items")
                
                # Сохраняем данные в соответствующие буферы
                if channel == 'books':
                    self.order_book_data = data['data']
                elif channel == 'trades':
                    self.trade_data = data['data']
                elif channel == 'tickers':
                    self.ticker_data = data['data']
                
                # Обновляем фичи и выводим каждые 10 сообщений
                self.update_and_print_features()
                
        except Exception as e:
            print(f"❌ Message error: {e}")
    
    def update_and_print_features(self):
        """Обновляет и выводит фичи каждые 10 сообщений"""
        if self.message_count % 10 == 0:
            features = feature_engine.get_all_features(
                self.order_book_data, 
                self.trade_data, 
                self.ticker_data
            )
            
            print("\n" + "="*50)
            print("🎯 REAL-TIME FEATURES:")
            print(f"📊 Order Book Imbalance: {features['order_book_imbalance']:.3f}")
            print(f"📏 Spread: {features['spread_percent']:.4f}%")
            print(f"📈 Cumulative Delta: {features['cumulative_delta']:.4f}")
            print(f"💰 Funding Rate: {features['funding_rate']:.6f}")
            print(f"🔄 Trades: {features['buy_trades']} buy / {features['sell_trades']} sell")
            print("="*50 + "\n")
    
    def on_error(self, ws, error):
        print(f"❌ WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 WebSocket closed")
        # Автопереподключение
        time.sleep(5)
        self.start()
    
    def on_open(self, ws):
        print(f"🔌 WebSocket connected at {datetime.now()}")
        # Подписываемся на каналы
        from config import CHANNELS, SYMBOL
        for channel in CHANNELS:
            subscribe_msg = {
                "op": "subscribe",
                "args": [
                    {
                        "channel": channel,
                        "instId": SYMBOL
                    }
                ]
            }
            ws.send(json.dumps(subscribe_msg))
            print(f"📡 Subscribed to: {channel} for {SYMBOL}")
    
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
