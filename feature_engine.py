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
        
    def calculate_order_book_imbalance(self, order_book_data):
        """Рассчитывает imbalance из стакана"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 0.5
            if 'asks' not in order_book_data[0] or 'bids' not in order_book_data[0]:
                return 0.5
            if len(order_book_data[0]['bids']) == 0 or len(order_book_data[0]['asks']) == 0:
                return 0.5
                
            book = order_book_data[0]
            bids = book['bids']
            asks = book['asks']
            
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
            return 0.5
    
    def calculate_spread(self, order_book_data):
        """Рассчитывает спред из стакана"""
        try:
            if not order_book_data or len(order_book_data) == 0:
                return 0
            if 'asks' not in order_book_data[0] or 'bids' not in order_book_data[0]:
                return 0
            if len(order_book_data[0]['bids']) == 0 or len(order_book_data[0]['asks']) == 0:
                return 0
                
            book = order_book_data[0]
            best_bid = float(book['bids'][0][0])
            best_ask = float(book['asks'][0][0])
            
            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100
            
            return spread_percent
            
        except Exception as e:
            return 0
    
    def update_cumulative_delta(self, trade_data):
        """Обновляет cumulative delta из ленты сделок"""
        try:
            if not trade_data:
                return self.cumulative_delta
                
            for trade in trade_data:
                if 'side' in trade:
                    if trade['side'] == 'buy':
                        self.cumulative_delta += float(trade.get('sz', 0))
                        self.trade_counts['buy'] += 1
                    elif trade['side'] == 'sell':
                        self.cumulative_delta -= float(trade.get('sz', 0))
                        self.trade_counts['sell'] += 1
                    
            return self.cumulative_delta
            
        except Exception as e:
            return self.cumulative_delta
    
    def extract_funding_rate(self, ticker_data):
        """Извлекает funding rate из тикеров"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            ticker = ticker_data[0]
            funding_rate = float(ticker.get('fundingRate', 0))
            return funding_rate
        except:
            return 0
    
    def get_current_price(self, ticker_data):
        """Извлекает текущую цену из тикеров"""
        try:
            if not ticker_data or len(ticker_data) == 0:
                return 0
            
            ticker = ticker_data[0]
            
            # Отладочный вывод (только первые 5 раз)
            if self.price_debug_count < 5:
                print(f"🔍 DEBUG TICKER [{self.price_debug_count}]: {ticker}")
                self.price_debug_count += 1
            
            # Пробуем разные поля где может быть цена
            if 'last' in ticker and ticker['last']:
                price = float(ticker['last'])
            elif 'lastPrice' in ticker and ticker['lastPrice']:
                price = float(ticker['lastPrice']) 
            elif 'close' in ticker and ticker['close']:
                price = float(ticker['close'])
            elif 'askPx' in ticker and 'bidPx' in ticker:
                # Берем среднюю между лучшими ценами
                price = (float(ticker['askPx']) + float(ticker['bidPx'])) / 2
            elif 'markPx' in ticker:
                price = float(ticker['markPx'])
            else:
                # Если ничего не нашли, используем стакан
                return self.get_price_from_orderbook()
            
            return price
            
        except Exception as e:
            if self.price_debug_count < 10:
                print(f"❌ DEBUG: Price extraction error: {e}")
                self.price_debug_count += 1
            return 0
    
    def get_price_from_orderbook(self):
        """Получает цену из стакана как среднюю между bid/ask"""
        # Этот метод нужно будет вызвать если в тикерах нет цены
        # Пока возвращаем 0
        return 0
    
    def calculate_target(self, current_price, future_price, threshold=0.1):
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
    
    def update_price_history(self, current_price, features):
        """Обновляет историю цен и фичей"""
        if current_price == 0:
            if self.price_debug_count < 10:
                print("❌ DEBUG: Current price is 0, skipping history update")
                self.price_debug_count += 1
            return None
            
        current_time = datetime.now()
        
        # Сохраняем текущие данные
        self.price_history.append({
            'timestamp': current_time,
            'price': current_price,
            'features': features.copy()
        })
        
        # Очищаем старые данные (храним 10 минут)
        ten_min_ago = current_time - timedelta(minutes=10)
        self.price_history = [
            p for p in self.price_history 
            if p['timestamp'] > ten_min_ago
        ]
        
        # ОТЛАДКА: выводим размер истории
        if len(self.price_history) % 50 == 0:
            print(f"🔍 DEBUG: Price history size = {len(self.price_history)}, current_price = {current_price}")
        
        # Обновляем target для записей 1-минутной давности
        one_min_ago = current_time - timedelta(minutes=1)
        target_updated = False
        
        for data_point in self.price_history:
            if (data_point['timestamp'] <= one_min_ago and 
                'target' not in data_point['features']):
                
                future_price = current_price
                current_price_at_time = data_point['price']
                
                target = self.calculate_target(current_price_at_time, future_price)
                data_point['features']['target'] = target
                target_updated = True
                
                # Логируем данные с target
                price_change = (future_price - current_price_at_time) / current_price_at_time * 100
                print(f"🎯 TARGET CALCULATED: {target} (price change: {price_change:.3f}%)")
                
                # Возвращаем обновленные фичи для сохранения
                return data_point['features']
        
        return None
    
    def get_all_features(self, order_book_data, trade_data, ticker_data):
        """Собирает все фичи вместе"""
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

# Глобальный экземпляр
feature_engine = FeatureEngine()
