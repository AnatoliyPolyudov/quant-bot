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
        self.target_horizon = 10  # 🔧 Уменьшено до 10 секунд
        self.target_threshold = 0.08  # 🔧 Увеличено до 0.08%
        self.trade_history = []  # 🔧 Исправлено: храним историю трейдов
        self.volatility_window = 30  # 🔧 Добавлено: окно для волатильности
        self.ob_debug_shown = False
        
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
            
            valid_bids = [bid for bid in bids[:bid_levels] if len(bid) >= 2 and float(bid[1]) > 0]
            valid_asks = [ask for ask in asks[:ask_levels] if len(ask) >= 2 and float(ask[1]) > 0]
            
            if not valid_bids or not valid_asks:
                return 0.5
            
            bid_volume = sum(float(bid[1]) for bid in valid_bids)
            ask_volume = sum(float(ask[1]) for ask in valid_asks)
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.5
                
            imbalance = bid_volume / total_volume
            imbalance = max(0.01, min(0.99, imbalance))
            
            return imbalance
            
        except Exception as e:
            return 0.5
    
    def calculate_spread(self, order_book_data):
        """Рассчитывает спред с улучшенной логикой"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 0.1
                
            book = order_book_data[0]
            
            if 'bids' not in book or 'asks' not in book:
                return 0.1
            if len(book['bids']) == 0 or len(book['asks']) == 0:
                return 0.1
            
            if len(book['bids'][0]) < 1 or len(book['asks'][0]) < 1:
                return 0.1
                
            best_bid = float(book['bids'][0][0])
            best_ask = float(book['asks'][0][0])
            
            if best_bid <= 0 or best_ask <= 0:
                return 0.1
                
            if best_bid >= best_ask:
                return 0.1
                
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2
            spread_percent = (spread / mid_price) * 100  # 🔧 Исправлено: mid price вместо bid
            
            if spread_percent < 0 or spread_percent > 1.0:
                return 0.1
                
            return spread_percent
            
        except Exception as e:
            return 0.1
    
    def update_cumulative_delta(self, trade_data):
        """🔧 ИСПРАВЛЕННЫЙ: Rolling delta за 20 секунд"""
        try:
            current_time = time.time()
            
            # Добавляем новые трейды в историю
            for trade in trade_data:
                if 'side' in trade and 'sz' in trade:
                    try:
                        size = float(trade['sz'])
                        sign = 1 if trade['side'] == 'buy' else -1
                        self.trade_history.append((current_time, sign * size))
                        
                        if trade['side'] == 'buy':
                            self.trade_counts['buy'] += 1
                        else:
                            self.trade_counts['sell'] += 1
                    except (ValueError, TypeError):
                        continue
            
            # Удаляем трейды старше 20 секунд
            self.trade_history = [(ts, vol) for ts, vol in self.trade_history 
                                 if current_time - ts <= 20]
            
            # Считаем delta как сумму за последние 20 секунд
            self.cumulative_delta = sum(vol for ts, vol in self.trade_history)
            
            return self.cumulative_delta
            
        except Exception as e:
            return self.cumulative_delta
    
    def calculate_volatility(self):
        """🔧 ДОБАВЛЕНО: Расчет волатильности"""
        try:
            if len(self.price_history) < 2:
                return 0
                
            # Берем последние N цен для расчета волатильности
            prices = [dp['price'] for dp in self.price_history[-self.volatility_window:]]
            if len(prices) < 2:
                return 0
                
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] != 0:
                    ret = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(ret)
            
            if len(returns) < 2:
                return 0
                
            volatility = np.std(returns) * 100  # В процентах
            return volatility
            
        except Exception as e:
            return 0
    
    def extract_funding_rate(self, ticker_data):
        """Извлекает funding rate"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            ticker = ticker_data[0]
            return float(ticker.get('fundingRate', 0))
        except Exception as e:
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
                    price = float(ticker[field])
                    if 1000 < price < 200000:
                        return price
            
            if 'askPx' in ticker and 'bidPx' in ticker:
                if ticker['askPx'] and ticker['bidPx']:
                    bid = float(ticker['bidPx'])
                    ask = float(ticker['askPx'])
                    if bid > 0 and ask > 0 and bid < ask:
                        price = (bid + ask) / 2
                        if 1000 < price < 200000:
                            return price
            
            return 0
            
        except Exception as e:
            return 0
    
    def calculate_target(self, current_price, future_price):
        """Рассчитывает target с улучшенным порогом"""
        if current_price == 0 or future_price == 0:
            return 0
            
        price_change = (future_price - current_price) / current_price * 100
        
        if price_change > self.target_threshold:    # 0.08%
            return 1
        elif price_change < -self.target_threshold: # -0.08%
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
        """Обновляет историю с ИСПРАВЛЕННОЙ логикой возврата"""
        if current_price == 0:
            return None
            
        current_time = datetime.now()
        
        # Дебаг каждые 30 секунд
        current_timestamp = time.time()
        if current_timestamp - self.last_history_debug > 30:
            self.last_history_debug = current_timestamp
            oldest_age = 0
            if self.price_history:
                oldest_age = (current_time - self.price_history[0]['timestamp']).total_seconds()
            
            target_time = current_time - timedelta(seconds=self.target_horizon)
            eligible_count = sum(1 for dp in self.price_history if dp['timestamp'] <= target_time)
            calculated_count = sum(1 for dp in self.price_history if dp.get('target_calculated', False))
            
            print(f"📈 History: {len(self.price_history)} records, oldest: {oldest_age:.1f}s")
            print(f"🔍 Target: {eligible_count} eligible, {calculated_count} calculated")
        
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
            'target_calculated': False
        })
        
        if len(self.price_history) > 600:
            self.price_history = self.price_history[-600:]
        
        # РАСЧЕТ TARGET
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
        
        # 🔧 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: ВОЗВРАЩАЕМ ВСЕГДА фичи с target
        if targets_calculated > 0:
            # Ищем ЛЮБУЮ запись с рассчитанным target
            for data_point in reversed(self.price_history):
                if 'target' in data_point['features']:
                    return data_point['features']
        
        return None
    
    def get_all_features(self, order_book_data, trade_data, ticker_data):
        """Собирает все фичи с волатильностью"""
        if not self.should_update_features():
            if self.price_history:
                return self.price_history[-1]['features']
            else:
                return self.create_empty_features()
        
        self.update_cumulative_delta(trade_data)
        
        current_price = self.get_current_price(ticker_data)
        
        if current_price == 0:
            if self.price_history:
                return self.price_history[-1]['features']
            else:
                return self.create_empty_features()
        
        # 🔧 ДОБАВЛЕНО: Расчет волатильности
        volatility = self.calculate_volatility()
        
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
            'volatility': volatility,  # 🔧 НОВАЯ ФИЧА
            'target': 0
        }
        
        updated_features = self.update_price_history(current_price, features)
        
        if updated_features is not None:
            return updated_features
        else:
            return features

    def create_empty_features(self):
        """Создает пустые фичи"""
        return {
            'timestamp': datetime.now().isoformat(),
            'order_book_imbalance': 0.5,
            'spread_percent': 0.1,
            'cumulative_delta': self.cumulative_delta,
            'funding_rate': 0,
            'buy_trades': self.trade_counts['buy'],
            'sell_trades': self.trade_counts['sell'],
            'total_trades': self.trade_counts['buy'] + self.trade_counts['sell'],
            'current_price': 0,
            'volatility': 0,
            'target': 0
        }

# Глобальный экземпляр
feature_engine = FeatureEngine()
