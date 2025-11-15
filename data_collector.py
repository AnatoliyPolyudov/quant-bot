# data_collector.py
import websocket
import json
import threading
import time
from datetime import datetime
import ssl
from feature_engine import feature_engine
from data_logger import data_logger
from baseline_strategy import baseline_strategy
from config import config  # 🔧 ИМПОРТИРУЕМ НОВУЮ КОНФИГУРАЦИЮ

class OKXDataCollector:
    def __init__(self):
        self.ws = None
        self.data_buffer = []
        self.message_count = 0
        self.last_feature_print = 0
        self.last_data_log = 0
        self.connection_start_time = 0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = config.data.RECONNECT_ATTEMPTS  # 🔧 ИСПОЛЬЗУЕМ КОНФИГ
        
        # Раздельные буферы для разных типов данных
        self.order_book_data = []
        self.trade_data = []
        self.ticker_data = []
        
        # Статистика сбора данных
        self.stats = {
            'messages_received': 0,
            'features_processed': 0,
            'last_successful_update': 0,
            'connection_quality': 'UNKNOWN',
            'data_quality_issues': 0
        }
        
        # Время последнего обновления по типам данных
        self.last_update_time = {
            'order_book': 0,
            'trades': 0,
            'ticker': 0
        }
        
    def on_message(self, ws, message):
        """Улучшенный обработчик входящих сообщений"""
        try:
            data = json.loads(message)
            self.message_count += 1
            self.stats['messages_received'] += 1
            
            # Показываем структуру только первых 2 сообщений каждого типа
            if self.message_count <= 2:
                print(f"\n🔍 RAW MESSAGE #{self.message_count}:")
                print(f"   Keys: {list(data.keys())}")
                if 'arg' in data:
                    print(f"   Channel: {data['arg']}")
                if 'data' in data:
                    print(f"   Data length: {len(data['data'])}")
                    if len(data['data']) > 0:
                        print(f"   First item keys: {list(data['data'][0].keys())}")
                        sample = str(data['data'][0])[:150]
                        print(f"   Sample: {sample}...")
            
            # Обрабатываем разные типы сообщений
            if 'event' in data:
                if data['event'] != 'subscribe':  # Показываем только ошибки
                    print(f"⚡ Event: {data['event']} - {data.get('msg', '')}")
            elif 'data' in data:
                channel = data.get('arg', {}).get('channel', 'unknown')
                current_time = time.time()
                
                # Сохраняем данные в соответствующие буферы
                if channel == 'books':
                    self.order_book_data = data['data']
                    self.last_update_time['order_book'] = current_time
                    
                    # Проверяем структуру стакана
                    if self.message_count <= 2 and len(data['data']) > 0:
                        book = data['data'][0]
                        bids_count = len(book.get('bids', []))
                        asks_count = len(book.get('asks', []))
                        print(f"   📚 Order Book - Bids: {bids_count}, Asks: {asks_count}")
                        
                elif channel == 'trades':
                    self.trade_data = data['data']
                    self.last_update_time['trades'] = current_time
                    
                    if self.message_count <= 2 and len(data['data']) > 0:
                        trade = data['data'][0]
                        print(f"   💰 Trade - Side: {trade.get('side')}, Size: {trade.get('sz')}, Price: {trade.get('px')}")
                        
                elif channel == 'tickers':
                    self.ticker_data = data['data']
                    self.last_update_time['ticker'] = current_time
                    
                    if self.message_count <= 2 and len(data['data']) > 0:
                        ticker = data['data'][0]
                        print(f"   📈 Ticker - Last: {ticker.get('last')}, Funding: {ticker.get('fundingRate')}")
                
                # Проверяем качество данных перед обновлением
                if self.is_data_quality_good():
                    self.update_features()
                else:
                    self.stats['data_quality_issues'] += 1
                    if self.stats['data_quality_issues'] % 10 == 0:
                        print(f"⚠️  Проблемы с качеством данных: {self.stats['data_quality_issues']}")
                
        except Exception as e:
            print(f"❌ Message error: {e}")
            self.stats['data_quality_issues'] += 1
    
    def is_data_quality_good(self):
        """Проверяет качество полученных данных"""
        try:
            current_time = time.time()
            
            # Проверяем, что у нас есть данные всех типов
            has_order_book = len(self.order_book_data) > 0
            has_trades = len(self.trade_data) > 0  
            has_ticker = len(self.ticker_data) > 0
            
            if not (has_order_book and has_trades and has_ticker):
                return False
            
            # Проверяем актуальность данных (не старше 10 секунд)
            max_age = 10
            for data_type, last_update in self.last_update_time.items():
                if current_time - last_update > max_age:
                    return False
            
            # Проверяем стакан на валидность
            if has_order_book:
                book = self.order_book_data[0]
                bids = book.get('bids', [])
                asks = book.get('asks', [])
                
                if len(bids) == 0 or len(asks) == 0:
                    return False
                    
                # Проверяем, что цены в стакане валидны
                best_bid = float(bids[0][0]) if len(bids[0]) > 0 else 0
                best_ask = float(asks[0][0]) if len(asks[0]) > 0 else 0
                
                if best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
                    return False
            
            return True
            
        except Exception as e:
            return False
    
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
        
        # Логируем данные
        data_logger.log_features(features)
        
        self.stats['features_processed'] += 1
        self.stats['last_successful_update'] = current_time
        
        # Выводим в консоль каждые 15 секунд с улучшенной информацией
        if current_time - self.last_feature_print > 15:
            self.last_feature_print = current_time
            
            # Обновляем статистику качества соединения
            self.update_connection_quality()
            
            print("\n" + "="*60)
            print(f"🎯 REAL-TIME FEATURES (Msg #{self.message_count})")
            print("="*60)
            
            # Основные фичи
            print(f"📊 Order Book Imbalance: {features['order_book_imbalance']:.3f}")
            print(f"📏 Spread: {features['spread_percent']:.6f}%")
            print(f"📈 Cumulative Delta: {features['cumulative_delta']:.4f}")
            print(f"💰 Funding Rate: {features['funding_rate']:.8f}")
            print(f"🔄 Trades: {features['buy_trades']} buy / {features['sell_trades']} sell")
            print(f"💵 Current Price: {features['current_price']:.1f}")
            print(f"🌊 Volatility: {features['volatility']:.4f}%")
            
            print(f"\n🤖 BASELINE STRATEGY:")
            print(f"   Decision: {strategy_result['decision']}")
            print(f"   Confidence: {strategy_result['confidence']:.1f}%")
            print(f"   Composite Score: {strategy_result['composite_score']:.3f}")
            print(f"   Market Regime: {strategy_result['market_regime']}")
            
            # Показываем топ-3 сигнала
            if strategy_result['signals']:
                print(f"   Top Signals:")
                for signal in strategy_result['signals'][:3]:
                    print(f"     {signal}")
            
            print(f"\n📊 DATA COLLECTION STATS:")
            print(f"   Messages: {self.stats['messages_received']}")
            print(f"   Features: {self.stats['features_processed']}")
            print(f"   Data Quality: {self.stats['connection_quality']}")
            print(f"   Last Update: {time.time() - self.stats['last_successful_update']:.1f}s ago")
            
            # Статус данных по типам
            print(f"   Data Status:")
            for data_type, last_update in self.last_update_time.items():
                age = current_time - last_update
                status = "✅" if age < 5 else "⚠️" if age < 10 else "❌"
                print(f"     {data_type}: {status} ({age:.1f}s)")
            
            print("="*60 + "\n")
    
    def update_connection_quality(self):
        """Оценивает качество соединения"""
        current_time = time.time()
        time_since_last_update = current_time - self.stats['last_successful_update']
        
        if time_since_last_update < 5:
            self.stats['connection_quality'] = "EXCELLENT"
        elif time_since_last_update < 10:
            self.stats['connection_quality'] = "GOOD" 
        elif time_since_last_update < 20:
            self.stats['connection_quality'] = "POOR"
        else:
            self.stats['connection_quality'] = "DISCONNECTED"
    
    def on_error(self, ws, error):
        print(f"❌ WebSocket error: {error}")
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > self.max_reconnect_attempts:
            print("❌ Превышено максимальное количество попыток переподключения")
            return
    
    def on_close(self, ws, close_status_code, close_msg):
        print(f"🔌 WebSocket closed: {close_status_code} - {close_msg}")
        # Автопереподключение с экспоненциальной задержкой
        if self.reconnect_attempts <= self.max_reconnect_attempts:
            delay = min(30, 2 ** self.reconnect_attempts)
            print(f"🔄 Переподключение через {delay} секунд...")
            time.sleep(delay)
            self.start()
        else:
            print("❌ Превышено максимальное количество попыток переподключения")
    
    def on_open(self, ws):
        print(f"🔌 WebSocket connected at {datetime.now()}")
        self.connection_start_time = time.time()
        self.reconnect_attempts = 0
        self.stats['connection_quality'] = "CONNECTED"
        
        # 🔧 ИСПОЛЬЗУЕМ КОНФИГ ДЛЯ ПОДПИСКИ
        for channel in config.data.CHANNELS:
            subscribe_msg = {
                "op": "subscribe",
                "args": [
                    {
                        "channel": channel,
                        "instId": config.data.SYMBOL  # 🔧 ИСПОЛЬЗУЕМ КОНФИГ
                    }
                ]
            }
            ws.send(json.dumps(subscribe_msg))
            print(f"📡 Subscribed to: {channel} for {config.data.SYMBOL}")
        
        # Инициализируем время обновления
        current_time = time.time()
        for data_type in self.last_update_time.keys():
            self.last_update_time[data_type] = current_time
    
    def get_connection_stats(self):
        """Возвращает статистику соединения"""
        current_time = time.time()
        uptime = current_time - self.connection_start_time if self.connection_start_time > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'messages_received': self.stats['messages_received'],
            'features_processed': self.stats['features_processed'],
            'connection_quality': self.stats['connection_quality'],
            'data_quality_issues': self.stats['data_quality_issues'],
            'reconnect_attempts': self.reconnect_attempts
        }
    
    def start(self):
        """Запуск сбора данных с улучшенной обработкой ошибок"""
        print(f"🚀 Starting data collector... (attempt {self.reconnect_attempts + 1})")
        
        try:
            self.ws = websocket.WebSocketApp(
                config.data.WS_URL,  # 🔧 ИСПОЛЬЗУЕМ КОНФИГ
                on_message=self.on_message,
                on_error=self.on_error, 
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # Настраиваем SSL контекст
            ssl_defaults = ssl.create_default_context()
            ssl_defaults.check_hostname = False
            ssl_defaults.verify_mode = ssl.CERT_NONE
            
            # Запускаем в отдельном потоке
            self.ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
                )
            )
            self.ws_thread.daemon = True
            self.ws_thread.start()
            print("✅ Data collector started successfully")
            
        except Exception as e:
            print(f"❌ Failed to start data collector: {e}")
            self.reconnect_attempts += 1
            if self.reconnect_attempts <= self.max_reconnect_attempts:
                time.sleep(config.data.RECONNECT_DELAY)  # 🔧 ИСПОЛЬЗУЕМ КОНФИГ
                self.start()

# Глобальный экземпляр
data_collector = OKXDataCollector()
