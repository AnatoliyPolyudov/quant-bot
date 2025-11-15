# data_collector.py
import websocket
import json
import threading
import time
from datetime import datetime
from feature_engine import feature_engine
from data_logger import data_logger
from baseline_strategy import baseline_strategy

class OKXDataCollector:
    def __init__(self):
        self.ws = None
        self.data_buffer = []
        self.message_count = 0
        self.last_feature_print = 0
        self.last_data_log = 0
        
        # Раздельные буферы для разных типов данных
        self.order_book_data = []
        self.trade_data = []
        self.ticker_data = []
        
    def on_message(self, ws, message):
        """Обработка входящих сообщений"""
        try:
            data = json.loads(message)
            self.message_count += 1
            
            # ДИАГНОСТИКА: показываем структуру первых сообщений
            if self.message_count <= 3:
                print(f"\n🔍 RAW MESSAGE #{self.message_count}:")
                print(f"   Keys: {list(data.keys())}")
                if 'arg' in data:
                    print(f"   Channel: {data['arg']}")
                if 'data' in data:
                    print(f"   Data length: {len(data['data'])}")
                    if len(data['data']) > 0:
                        print(f"   First item keys: {list(data['data'][0].keys())}")
                        print(f"   Sample: {str(data['data'][0])[:200]}...")
            
            # Обрабатываем разные типы сообщений
            if 'event' in data:
                if data['event'] != 'subscribe':  # Показываем только ошибки
                    print(f"⚡ Event: {data['event']} - {data.get('msg', '')}")
            elif 'data' in data:
                channel = data.get('arg', {}).get('channel', 'unknown')
                
                # Сохраняем данные в соответствующие буферы
                if channel == 'books':
                    self.order_book_data = data['data']
                    # Проверяем структуру стакана
                    if self.message_count <= 3 and len(data['data']) > 0:
                        book = data['data'][0]
                        print(f"   📚 Order Book - Bids: {len(book.get('bids', []))}, Asks: {len(book.get('asks', []))}")
                        
                elif channel == 'trades':
                    self.trade_data = data['data']
                    if self.message_count <= 3 and len(data['data']) > 0:
                        trade = data['data'][0]
                        print(f"   💰 Trade - Side: {trade.get('side')}, Size: {trade.get('sz')}")
                        
                elif channel == 'tickers':
                    self.ticker_data = data['data']
                    if self.message_count <= 3 and len(data['data']) > 0:
                        ticker = data['data'][0]
                        print(f"   📈 Ticker - Last: {ticker.get('last')}, Funding: {ticker.get('fundingRate')}")
                
                # Обновляем фичи и выводим/логируем
                self.update_features()
                
        except Exception as e:
            print(f"❌ Message error: {e}")
    
    def update_features(self):
        """Обновляет фичи и управляет выводом/логированием"""
        current_time = time.time()
        
        # Всегда обновляем фичи
        features = feature_engine.get_all_features(
            self.order_book_data, 
            self.trade_data, 
            self.ticker_data
        )
        
        # Анализ бейзлайн-стратегией
        strategy_result = baseline_strategy.analyze_signal(features)
        
        # Логируем данные каждую минуту (только если есть реальные данные)
        if current_time - self.last_data_log > 60 and features.get('current_price', 0) > 0:
            self.last_data_log = current_time
            data_logger.log_features(features)
        
        # Выводим в консоль каждые 10 секунд (чаще для отладки)
        if current_time - self.last_feature_print > 10:
            self.last_feature_print = current_time
            
            print("\n" + "="*50)
            print(f"🎯 REAL-TIME FEATURES (Msg #{self.message_count})")
            print("="*50)
            
            print(f"📊 Order Book Imbalance: {features['order_book_imbalance']:.3f}")
            print(f"📏 Spread: {features['spread_percent']:.6f}%")
            print(f"📈 Cumulative Delta: {features['cumulative_delta']:.4f}")
            print(f"💰 Funding Rate: {features['funding_rate']:.8f}")
            print(f"🔄 Trades: {features['buy_trades']} buy / {features['sell_trades']} sell")
            print(f"💵 Current Price: {features['current_price']}")
            
            print(f"\n🤖 BASELINE DECISION: {strategy_result['decision']}")
            print(f"🎯 Confidence: {strategy_result['confidence']:.1f}%")
            
            for signal in strategy_result['signals']:
                print(f"   {signal}")
                
            print(f"📊 Data buffers - OB: {len(self.order_book_data)}, Trades: {len(self.trade_data)}, Ticker: {len(self.ticker_data)}")
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

# Глобальный экземпляр - ОБЯЗАТЕЛЬНО В КОНЦЕ ФАЙЛА
data_collector = OKXDataCollector()
