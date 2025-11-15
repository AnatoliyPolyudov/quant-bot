# feature_engine.py
from datetime import datetime, timedelta
import time
import numpy as np

class FeatureEngine:
    def __init__(self):
        self.cumulative_delta = 0
        self.trade_counts = {'buy': 0, 'sell': 0}
        self.price_history = []
        self.feature_history = []
        self.last_update_time = 0
        self.update_interval = 1
        self.last_history_debug = 0
        self.target_horizon = 20  # секунд для target
        self.target_threshold = 0.02  
        self.delta_window = []  # Rolling window для delta
        self.max_delta_window = 100  # ~30 секунд истории
        
    def calculate_order_book_imbalance(self, order_book_data):
        """Рассчитывает imbalance из стакана"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 0.5
                
            book = order_book_data[0]
            
            if 'bids' not in book or 'asks' not in book:
                return 0.5
            if len(book['bids']) == 0 or len(book['asks']) == 0:
                return 0.5
                
            bids = book['bids']
            asks = book['asks']
            
            bid_levels = min(len(bids), 3)
            ask_levels = min(len(asks), 3)
            
            if bid_levels == 0 or ask_levels == 0:
                return 0.5
            
            bid_volume = sum(float(bid[1]) for bid in bids[:bid_levels] if len(bid) >= 2)
            ask_volume = sum(float(ask[1]) for ask in asks[:ask_levels] if len(ask) >= 2)
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.5
                
            imbalance = bid_volume / total_volume
            return max(0.0, min(1.0, imbalance))
            
        except Exception as e:
            print(f"❌ Order book error: {e}")
            return 0.5
    
    def calculate_spread(self, order_book_data):
        """Рассчитывает спред"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 100.0  # Большое значение вместо 0
                
            book = order_book_data[0]
            
            if 'bids' not in book or 'asks' not in book:
                return 100.0
            if len(book['bids']) == 0 or len(book['asks']) == 0:
                return 100.0
                
            best_bid = float(book['bids'][0][0])
            best_ask = float(book['asks'][0][0])
            
            if best_bid >= best_ask:
                return 100.0
                
            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100
            
            return spread_percent if spread_percent >= 0 else 100.0
            
        except Exception as e:
            print(f"❌ Spread calculation error: {e}")
            return 100.0
    
    def update_cumulative_delta(self, trade_data):
        """Обновляет ROLLING cumulative delta"""
        try:
            if not trade_data:
                return self.cumulative_delta
                
            current_delta = 0
            for trade in trade_data:
                if 'side' in trade and 'sz' in trade:
                    try:
                        size = float(trade['sz'])
                        if trade['side'] == 'buy':
                            current_delta += size
                            self.trade_counts['buy'] += 1
                        elif trade['side'] == 'sell':
                            current_delta -= size
                            self.trade_counts['sell'] += 1
                    except (ValueError, TypeError):
                        continue
            
            # Добавляем в rolling window
            self.delta_window.append(current_delta)
            if len(self.delta_window) > self.max_delta_window:
                self.delta_window.pop(0)
            
            # Обновляем cumulative delta как сумму окна
            self.cumulative_delta = sum(self.delta_window)
                    
            return self.cumulative_delta
            
        except Exception as e:
            print(f"❌ Cumulative delta error: {e}")
            return self.cumulative_delta
    
    def extract_funding_rate(self, ticker_data):
        """Извлекает funding rate"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            ticker = ticker_data[0]
            return float(ticker.get('fundingRate', 0))
        except Exception as e:
            print(f"❌ Funding rate error: {e}")
            return 0
    
    def get_current_price(self, ticker_data):
        """Извлекает текущую цену"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            
            ticker = ticker_data[0]
            
            price_fields = ['last', 'lastPrice', 'close', 'markPx']
            for field in price_fields:
                if field in ticker and ticker[field]:
                    return float(ticker[field])
            
            if 'askPx' in ticker and 'bidPx' in ticker:
                if ticker['askPx'] and ticker['bidPx']:
                    return (float(ticker['askPx']) + float(ticker['bidPx'])) / 2
            
            return 0
            
        except Exception as e:
            print(f"❌ Price extraction error: {e}")
            return 0
    
    def calculate_target(self, current_price, future_price):
        """Рассчитывает target с реалистичным порогом"""
        if current_price == 0 or future_price == 0:
            return 0
            
        price_change = (future_price - current_price) / current_price * 100
        
        if price_change > self.target_threshold:    # 0.05%
            return 1
        elif price_change < -self.target_threshold: # -0.05%
            return -1
        else:
            return 0
    
    def should_update_features(self):
        """Проверяет, нужно ли обновлять фичи"""
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            return True
        return False
    
    def update_price_history(self, current_price, features):
        """Обновляет историю с исправленной логикой target"""
        if current_price == 0:
            return None
            
        current_time = datetime.now()
        
        # Дебаг каждые 10 секунд
        current_timestamp = time.time()
        if current_timestamp - self.last_history_debug > 10:
            self.last_history_debug = current_timestamp
            oldest_age = 0
            if self.price_history:
                oldest_age = (current_time - self.price_history[0]['timestamp']).total_seconds()
            
            print(f"📈 History: {len(self.price_history)} records, oldest: {oldest_age:.1f}s")
        
        # Ограничение частоты
        if len(self.price_history) > 0:
            last_time = self.price_history[-1]['timestamp']
            time_diff = (current_time - last_time).total_seconds()
            if time_diff < 0.5:
                return None
        
        # Добавляем в историю
        self.price_history.append({
            'timestamp': current_time,
            'price': current_price,
            'features': features.copy(),
            'target_calculated': False  # Флаг что target уже рассчитан
        })
        
        # Увеличиваем историю до 600 записей (~5 минут)
        if len(self.price_history) > 600:
            self.price_history = self.price_history[-600:]
        
        # РАСЧЕТ TARGET только для записей старше target_horizon
        target_time = current_time - timedelta(seconds=self.target_horizon)
        targets_calculated = 0
        
        for data_point in self.price_history:
            if (data_point['timestamp'] <= target_time and 
                not data_point['target_calculated']):
                
                future_price = current_price
                current_price_at_time = data_point['price']
                
                target = self.calculate_target(current_price_at_time, future_price)
                data_point['features']['target'] = target
                data_point['target_calculated'] = True
                targets_calculated += 1
                
                # Логируем только значимые изменения
                price_change = (future_price - current_price_at_time) / current_price_at_time * 100
                if abs(price_change) > self.target_threshold:
                    print(f"🎯 TARGET: {target} (change: {price_change:.3f}%)")
        
        if targets_calculated > 0:
            print(f"✅ Calculated {targets_calculated} targets")
            
            # Возвращаем последние фичи с target
            for data_point in reversed(self.price_history):
                if 'target' in data_point['features']:
                    return data_point['features']
        
        return None
    
    def get_all_features(self, order_book_data, trade_data, ticker_data):
        """Собирает все фичи"""
        if not self.should_update_features():
            if self.price_history:
                return self.price_history[-1]['features']
            else:
                return self.create_empty_features()
        
        self.update_cumulative_delta(trade_data)
        
        current_price = self.get_current_price(ticker_data)
        
        features = {
            'timestamp': datetime.now().isoformat(),
            'order_book_imbalance': self.calculate_order_book_imbalance(order_book_data),
            'spread_percent': self.calculate_spread(order_book_data),
            'cumulative_delta': self.cumulative_delta,
            'funding_rate': self.extract_funding_rate(ticker_data),
            'buy_trades': self.trade_counts['buy'],
            'sell_trades': self.trade_counts['sell'],
            'total_trades': self.trade_counts['buy'] + self.trade_counts['sell'],
            'current_price': current_price,
            'target': 0
        }
        
        updated_features = self.update_price_history(current_price, features)
        if updated_features:
            return updated_features
        
        return features
    
    def create_empty_features(self):
        """Создает пустые фичи"""
        return {
            'timestamp': datetime.now().isoformat(),
            'order_book_imbalance': 0.5,
            'spread_percent': 0,
            'cumulative_delta': self.cumulative_delta,
            'funding_rate': 0,
            'buy_trades': self.trade_counts['buy'],
            'sell_trades': self.trade_counts['sell'],
            'total_trades': self.trade_counts['buy'] + self.trade_counts['sell'],
            'current_price': 0,
            'target': 0
        }

# Глобальный экземпляр
feature_engine = FeatureEngine()
