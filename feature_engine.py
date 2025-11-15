# feature_engine.py
from datetime import datetime, timedelta

class FeatureEngine:
    def __init__(self):
        self.cumulative_delta = 0
        self.trade_counts = {'buy': 0, 'sell': 0}
        self.price_history = []  # храним историю цен для расчета target
        self.feature_history = []  # храним фичи с временными метками
        
    def calculate_order_book_imbalance(self, order_book_data):
        """Рассчитывает imbalance из стакана"""
        try:
            if not order_book_data or 'asks' not in order_book_data[0] or 'bids' not in order_book_data[0]:
                return 0.5
                
            book = order_book_data[0]
            bids = book['bids']
            asks = book['asks']
            
            bid_volume = sum(float(bid[1]) for bid in bids[:3])
            ask_volume = sum(float(ask[1]) for ask in asks[:3])
            
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                return 0.5
                
            imbalance = bid_volume / total_volume
            return imbalance
            
        except Exception as e:
            print(f"❌ Order book imbalance error: {e}")
            return 0.5
    
    def calculate_spread(self, order_book_data):
        """Рассчитывает спред из стакана"""
        try:
            if not order_book_data or 'asks' not in order_book_data[0] or 'bids' not in order_book_data[0]:
                return 0
                
            book = order_book_data[0]
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
                if 'side' in trade:
                    if trade['side'] == 'buy':
                        self.cumulative_delta += float(trade.get('sz', 0))
                        self.trade_counts['buy'] += 1
                    elif trade['side'] == 'sell':
                        self.cumulative_delta -= float(trade.get('sz', 0))
                        self.trade_counts['sell'] += 1
                    
            return self.cumulative_delta
            
        except Exception as e:
            print(f"❌ Cumulative delta error: {e}")
            return self.cumulative_delta
    
    def extract_funding_rate(self, ticker_data):
        """Извлекает funding rate из тикеров"""
        try:
            if not ticker_data:
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
            if not ticker_data:
                return 0
            ticker = ticker_data[0]
            return float(ticker.get('last', 0))
        except Exception as e:
            print(f"❌ Price extraction error: {e}")
            return 0
    
    def calculate_target(self, current_price, future_price, threshold=0.3):
        """Рассчитывает трехклассовую цель (-1/0/+1)"""
        if current_price == 0 or future_price == 0:
            return 0
            
        price_change = (future_price - current_price) / current_price * 100
        
        if price_change > threshold:    # рост > 0.3%
            return 1
        elif price_change < -threshold: # падение > 0.3%
            return -1
        else:                           # движение в пределах ±0.3%
            return 0
    
    def update_price_history(self, current_price, features):
        """Обновляет историю цен и фичей"""
        timestamp = datetime.now()
        
        # Сохраняем текущие данные
        self.price_history.append({
            'timestamp': timestamp,
            'price': current_price,
            'features': features.copy()
        })
        
        # Очищаем старые данные (храним 1 час)
        one_hour_ago = timestamp - timedelta(hours=1)
        self.price_history = [
            p for p in self.price_history 
            if p['timestamp'] > one_hour_ago
        ]
        
        # Обновляем target для старых записей (5 минут назад)
        five_min_ago = timestamp - timedelta(minutes=5)
        for data_point in self.price_history:
            if data_point['timestamp'] <= five_min_ago:
                # Находим текущую цену для расчета target
                future_price = current_price
                current_price_at_time = data_point['price']
                
                target = self.calculate_target(current_price_at_time, future_price)
                data_point['features']['target'] = target
    
    def get_all_features(self, order_book_data, trade_data, ticker_data):
        """Собирает все фичи вместе"""
        # Обновляем cumulative delta
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
            'target': 0  # будет рассчитан позже
        }
        
        # Обновляем историю для расчета target
        self.update_price_history(current_price, features)
        
        return features

# Глобальный экземпляр
feature_engine = FeatureEngine()
