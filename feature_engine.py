# feature_engine.py
from datetime import datetime

class FeatureEngine:
    def __init__(self):
        self.cumulative_delta = 0
        self.trade_counts = {'buy': 0, 'sell': 0}
        
    def calculate_order_book_imbalance(self, order_book_data):
        """Рассчитывает imbalance из стакана"""
        try:
            if not order_book_data or 'asks' not in order_book_data[0] or 'bids' not in order_book_data[0]:
                return 0.5  # нейтральное значение
                
            book = order_book_data[0]
            bids = book['bids']
            asks = book['asks']
            
            # Суммируем объемы на первых 3 уровнях
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
                # OKX передает сторону в поле 'side'
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
    
    def get_all_features(self, order_book_data, trade_data, ticker_data):
        """Собирает все фичи вместе"""
        # Обновляем cumulative delta
        self.update_cumulative_delta(trade_data)
        
        features = {
            'timestamp': datetime.now().isoformat(),
            'order_book_imbalance': self.calculate_order_book_imbalance(order_book_data),
            'spread_percent': self.calculate_spread(order_book_data),
            'cumulative_delta': self.cumulative_delta,
            'funding_rate': self.extract_funding_rate(ticker_data),
            'buy_trades': self.trade_counts['buy'],
            'sell_trades': self.trade_counts['sell'],
            'total_trades': self.trade_counts['buy'] + self.trade_counts['sell']
        }
        
        return features

# Глобальный экземпляр
feature_engine = FeatureEngine()
