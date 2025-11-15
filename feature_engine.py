# feature_engine.py
from datetime import datetime, timedelta
import time

class FeatureEngine:
    def __init__(self):
        self.cumulative_delta = 0
        self.trade_counts = {'buy': 0, 'sell': 0}
        self.price_history = []
        self.feature_history = []
        self.price_debug_count = 0
        self.target_calculated_count = 0
        self.last_update_time = 0
        self.update_interval = 1  # Обновлять фичи только раз в секунду
        self.last_history_debug = 0
        
    def calculate_order_book_imbalance(self, order_book_data):
        """Рассчитывает imbalance из стакана"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 0.5
            book = order_book_data[0]
            
            # Проверяем структуру данных OKX
            if 'bids' not in book or 'asks' not in book:
                return 0.5
            if len(book['bids']) == 0 or len(book['asks']) == 0:
                return 0.5
                
            bids = book['bids']
            asks = book['asks']
            
            # Берем только первые 3 уровня
            bid_levels = min(len(bids), 3)
            ask_levels = min(len(asks), 3)
            
            bid_volume = sum(float(bid[1]) for bid in bids[:bid_levels])
            ask_volume = sum(float(ask[1]) for ask in asks[:ask_levels])
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.5
                
            imbalance = bid_volume / total_volume
            return imbalance
            
        except Exception as e:
            print(f"❌ Order book error: {e}")
            return 0.5
    
    def calculate_spread(self, order_book_data):
        """Рассчитывает спред из стакана"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 0
            book = order_book_data[0]
            
            if 'bids' not in book or 'asks' not in book:
                return 0
            if len(book['bids']) == 0 or len(book['asks']) == 0:
                return 0
                
            best_bid = float(book['bids'][0][0])
            best_ask = float(book['asks'][0][0])
            
            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100
            
            return spread_percent
            
        except Exception as e:
            print(f"❌ Spread calculation error: {e}")
            return 0
    
    def update_cumulative_delta(self, trade_data):
        """Обновляет cumulative delta из ленты сделок"""
        try:
            if not trade_data:
                return self.cumulative_delta
                
            for trade in trade_data:
                if 'side' in trade and 'sz' in trade:
                    size = float(trade['sz'])
                    if trade['side'] == 'buy':
                        self.cumulative_delta += size
                        self.trade_counts['buy'] += 1
                    elif trade['side'] == 'sell':
                        self.cumulative_delta -= size
                        self.trade_counts['sell'] += 1
                    
            return self.cumulative_delta
            
        except Exception as e:
            print(f"❌ Cumulative delta error: {e}")
            return self.cumulative_delta
    
    def extract_funding_rate(self, ticker_data):
        """Извлекает funding rate из тикеров"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            ticker = ticker_data[0]
            funding_rate = float(ticker.get('fundingRate', 0))
            return funding_rate
        except Exception as e:
            print(f"❌ Funding rate error: {e}")
            return 0
    
    def get_current_price(self, ticker_data):
        """Извлекает текущую цену из тикеров"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            
            ticker = ticker_data[0]
            
            # Пробуем разные поля где может быть цена
            price_fields = ['last', 'lastPrice', 'close', 'markPx']
            for field in price_fields:
                if field in ticker and ticker[field]:
                    return float(ticker[field])
            
            # Если нет прямой цены, пробуем mid price
            if 'askPx' in ticker and 'bidPx' in ticker:
                if ticker['askPx'] and ticker['bidPx']:
                    return (float(ticker['askPx']) + float(ticker['bidPx'])) / 2
            
            return 0
            
        except Exception as e:
            print(f"❌ Price extraction error: {e}")
            return 0
    
    def calculate_target(self, current_price, future_price, threshold=0.005):  # УМЕНЬШЕНО до 0.005%
        """Рассчитывает трехклассовую цель (-1/0/+1)"""
        if current_price == 0 or future_price == 0:
            return 0
            
        price_change = (future_price - current_price) / current_price * 100
        
        if price_change > threshold:
            return 1
        elif price_change < -threshold:
            return -1
        else:
            return 0
    
    def should_update_features(self):
        """Проверяет, нужно ли обновлять фичи (ограничение частоты)"""
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            return True
        return False
    
    def update_price_history(self, current_price, features):
        """Обновляет историю цен и фичей (с ограничением частоты)"""
        if current_price == 0:
            return None
            
        current_time = datetime.now()
        
        # ДЕБАГ ИСТОРИИ: показываем прогресс каждые 5 секунд
        current_timestamp = time.time()
        if current_timestamp - self.last_history_debug > 5:
            self.last_history_debug = current_timestamp
            oldest_age = 0
            if self.price_history:
                oldest_age = (current_time - self.price_history[0]['timestamp']).total_seconds()
            
            # ДИАГНОСТИКА TARGET: проверяем почему не рассчитывается
            twenty_sec_ago = current_time - timedelta(seconds=20)
            eligible_for_target = 0
            already_has_target = 0
            for data_point in self.price_history:
                if data_point['timestamp'] <= twenty_sec_ago:
                    eligible_for_target += 1
                    if 'target' in data_point['features']:
                        already_has_target += 1
            
            print(f"📈 History: {len(self.price_history)} records, oldest: {oldest_age:.1f}s")
            print(f"🔍 Target diagnosis: {eligible_for_target} eligible, {already_has_target} already have target")
            
            # Показываем пример изменения цены для диагностики
            if len(self.price_history) >= 2:
                oldest_price = self.price_history[0]['price']
                newest_price = self.price_history[-1]['price']
                total_change = (newest_price - oldest_price) / oldest_price * 100
                print(f"💰 Price change overall: {total_change:.4f}% ({oldest_price} -> {newest_price})")
        
        # ОГРАНИЧЕНИЕ: добавляем в историю только если прошло достаточно времени
        if len(self.price_history) > 0:
            last_time = self.price_history[-1]['timestamp']
            time_diff = (current_time - last_time).total_seconds()
            if time_diff < 0.5:  # Не чаще чем раз в 0.5 секунды
                return None
        
        # Сохраняем текущие данные
        self.price_history.append({
            'timestamp': current_time,
            'price': current_price,
            'features': features.copy()
        })
        
        # Ограничиваем историю до 200 записей (УМЕНЬШЕНО для теста)
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-200:]
        
        # РАСЧЕТ TARGET: для записей старше 20 секунд
        twenty_sec_ago = current_time - timedelta(seconds=20)
        
        targets_calculated = 0
        for i, data_point in enumerate(self.price_history):
            if data_point['timestamp'] <= twenty_sec_ago:
                if 'target' not in data_point['features']:
                    future_price = current_price
                    current_price_at_time = data_point['price']
                    
                    target = self.calculate_target(current_price_at_time, future_price)
                    data_point['features']['target'] = target
                    self.target_calculated_count += 1
                    targets_calculated += 1
                    
                    # Логируем ВСЕ target расчеты для диагностики
                    price_change = (future_price - current_price_at_time) / current_price_at_time * 100
                    print(f"🎯 TARGET CALCULATED: {target} (change: {price_change:.4f}%) - {current_price_at_time} -> {future_price}")
        
        if targets_calculated > 0:
            print(f"✅ Calculated {targets_calculated} new targets, total: {self.target_calculated_count}")
            
            # Возвращаем последние фичи с target
            for data_point in reversed(self.price_history):
                if 'target' in data_point['features']:
                    return data_point['features']
        
        return None
    
    def get_all_features(self, order_book_data, trade_data, ticker_data):
        """Собирает все фичи вместе (с ограничением частоты)"""
        
        # ОГРАНИЧЕНИЕ ЧАСТОТЫ: обновляем не чаще чем раз в секунду
        if not self.should_update_features():
            # Возвращаем последние фичи вместо вычисления новых
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
        
        # Обновляем историю и получаем фичи с target (если есть)
        updated_features = self.update_price_history(current_price, features)
        if updated_features:
            return updated_features
        
        return features
    
    def create_empty_features(self):
        """Создает пустые фичи когда обновление не нужно"""
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
