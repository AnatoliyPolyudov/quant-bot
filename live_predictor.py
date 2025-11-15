# live_predictor.py
import joblib
import pandas as pd
from datetime import datetime
import time
from data_collector import data_collector
from feature_engine import feature_engine

class LivePredictor:
    def __init__(self):
        self.model = joblib.load("models/quant_model.pkl")
        self.feature_columns = [
            'order_book_imbalance', 'spread_percent', 'cumulative_delta',
            'funding_rate', 'buy_trades', 'sell_trades', 'total_trades'
        ]
        self.prediction_count = 0
        
    def make_prediction(self, features):
        """Делает предсказание на основе фич"""
        try:
            # Подготавливаем данные для модели
            X = pd.DataFrame([[
                features['order_book_imbalance'],
                features['spread_percent'],
                features['cumulative_delta'],
                features['funding_rate'],
                features['buy_trades'],
                features['sell_trades'],
                features['total_trades']
            ]], columns=self.feature_columns)
            
            # Предсказание
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0]
            
            self.prediction_count += 1
            
            return {
                'prediction': prediction,
                'probability': max(probability),
                'confidence': f"{max(probability)*100:.1f}%",
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return None
    
    def start_live_predictions(self):
        """Запускает предсказания в реальном времени"""
        print("🎯 LIVE ML PREDICTIONS STARTED...")
        print("=" * 50)
        
        last_print_time = 0
        
        while True:
            current_time = time.time()
            
            # Получаем свежие фичи
            features = feature_engine.get_all_features(
                data_collector.order_book_data,
                data_collector.trade_data, 
                data_collector.ticker_data
            )
            
            # Делаем предсказание каждые 10 секунд
            if current_time - last_print_time >= 10:
                last_print_time = current_time
                
                prediction = self.make_prediction(features)
                
                if prediction:
                    # Определяем цвет и символ для предсказания
                    if prediction['prediction'] == 1:
                        symbol = "🟢 LONG"
                        color = "\033[92m"  # Зеленый
                    elif prediction['prediction'] == -1:
                        symbol = "🔴 SHORT" 
                        color = "\033[91m"  # Красный
                    else:
                        symbol = "⚪ HOLD"
                        color = "\033[90m"  # Серый
                    
                    # Вывод предсказания
                    print(f"{color}🎯 [{prediction['timestamp']}] {symbol} | Confidence: {prediction['confidence']} | "
                          f"Imbalance: {features['order_book_imbalance']:.3f} | Delta: {features['cumulative_delta']:.1f}\033[0m")
                    
                    # Сравнение с бейзлайном
                    from baseline_strategy import baseline_strategy
                    baseline = baseline_strategy.analyze_signal(features)
                    print(f"   🤖 Baseline: {baseline['decision']} ({baseline['confidence']:.0f}%) vs ML: {symbol} ({prediction['confidence']})")
                    print("-" * 50)
            
            time.sleep(1)

if __name__ == "__main__":
    predictor = LivePredictor()
    predictor.start_live_predictions()
