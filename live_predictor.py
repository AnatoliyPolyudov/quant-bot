# live_predictor.py
import joblib
import pandas as pd
from datetime import datetime
import time
from data_collector import data_collector
from feature_engine import feature_engine
import os

class LivePredictor:
    def __init__(self):
        self.model = None
        self.feature_columns = [
            'order_book_imbalance', 'spread_percent', 'cumulative_delta',
            'funding_rate', 'buy_trades', 'sell_trades', 'total_trades'
        ]
        self.prediction_count = 0
        self.load_model()
        
    def load_model(self):
        """Загружает модель с проверкой"""
        try:
            model_path = "models/quant_model.pkl"
            if not os.path.exists(model_path):
                print("❌ Модель не найдена. Запустите train_model.py сначала.")
                return
                
            self.model = joblib.load(model_path)
            print("✅ Модель успешно загружена")
            
            # Проверяем классы модели
            if hasattr(self.model, 'classes_'):
                print(f"🎯 Классы модели: {self.model.classes_}")
                
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            self.model = None
    
    def make_prediction(self, features):
        """Делает предсказание с улучшенной диагностикой"""
        try:
            # 🔧 ФИКС: Проверяем, что модель загружена
            if self.model is None:
                return {
                    'prediction': 0,
                    'probability': 0,
                    'confidence': "0%",
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'error': 'Model not loaded'
                }
            
            # 🔧 ФИКС: Проверяем качество фич
            if features.get('current_price', 0) == 0:
                return {
                    'prediction': 0,
                    'probability': 0,
                    'confidence': "0%",
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'error': 'Invalid features'
                }
            
            # Подготавливаем данные для модели
            X = pd.DataFrame([[
                features.get('order_book_imbalance', 0.5),
                features.get('spread_percent', 0.01),
                features.get('cumulative_delta', 0),
                features.get('funding_rate', 0),
                features.get('buy_trades', 0),
                features.get('sell_trades', 0),
                features.get('total_trades', 0)
            ]], columns=self.feature_columns)
            
            # 🔧 ФИКС: Проверяем данные на NaN
            if X.isnull().any().any():
                print("❌ NaN values in features")
                return None
            
            # 🔧 ФИКС: Проверяем, что все фичи числовые
            for col in self.feature_columns:
                if col in X.columns:
                    X[col] = pd.to_numeric(X[col], errors='coerce')
            
            # Заполняем NaN если есть
            X = X.fillna(0)
            
            # Предсказание
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            
            # 🔧 ФИКС: Правильное определение confidence
            confidence = max(probabilities) * 100
            predicted_class = prediction
            
            self.prediction_count += 1
            
            # 🔧 ДИАГНОСТИКА: Показываем распределение вероятностей периодически
            if self.prediction_count <= 3 or self.prediction_count % 20 == 0:
                print(f"\n🔍 ML DIAGNOSTIC (Prediction #{self.prediction_count}):")
                print(f"   Features: imbalance={features.get('order_book_imbalance', 0):.3f}, "
                      f"delta={features.get('cumulative_delta', 0):.1f}")
                if hasattr(self.model, 'classes_'):
                    for i, cls in enumerate(self.model.classes_):
                        prob = probabilities[i] * 100
                        print(f"   Class {cls}: {prob:.1f}%")
                print(f"   Final prediction: {predicted_class}, confidence: {confidence:.1f}%")
            
            return {
                'prediction': predicted_class,
                'probability': max(probabilities),
                'confidence': f"{confidence:.1f}%",
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'probabilities': probabilities.tolist() if hasattr(probabilities, 'tolist') else probabilities
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return {
                'prediction': 0,
                'probability': 0,
                'confidence': "0%",
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'error': str(e)
            }
    
    def check_model_health(self):
        """Проверяет здоровье модели"""
        if self.model is None:
            return "❌ Модель не загружена"
        
        try:
            # Тестовое предсказание
            test_features = {
                'order_book_imbalance': 0.6,
                'spread_percent': 0.01,
                'cumulative_delta': 5,
                'funding_rate': 0.0001,
                'buy_trades': 10,
                'sell_trades': 5,
                'total_trades': 15
            }
            
            test_pred = self.make_prediction(test_features)
            if test_pred and 'error' not in test_pred:
                return f"✅ Модель работает (тест: {test_pred['prediction']})"
            else:
                return "❌ Ошибка тестового предсказания"
                
        except Exception as e:
            return f"❌ Ошибка проверки модели: {e}"
    
    def start_live_predictions(self):
        """Запускает предсказания в реальном времени"""
        print("🎯 LIVE ML PREDICTIONS STARTED...")
        print("=" * 60)
        
        # Проверяем модель
        health_status = self.check_model_health()
        print(f"🔧 Model Health: {health_status}")
        
        if self.model is None:
            print("❌ Не могу запустить предсказания - модель не загружена")
            print("💡 Запустите: python train_model.py")
            return
        
        last_print_time = 0
        consecutive_holds = 0
        
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
                
                if prediction and 'error' not in prediction:
                    # Определяем цвет и символ для предсказания
                    if prediction['prediction'] == 1:
                        symbol = "🟢 LONG"
                        color = "\033[92m"  # Зеленый
                        consecutive_holds = 0
                    elif prediction['prediction'] == -1:
                        symbol = "🔴 SHORT" 
                        color = "\033[91m"  # Красный
                        consecutive_holds = 0
                    else:
                        symbol = "⚪ HOLD"
                        color = "\033[90m"  # Серый
                        consecutive_holds += 1
                    
                    # 🔧 ФИКС: Предупреждение о многих HOLD подряд
                    hold_warning = ""
                    if consecutive_holds > 5:
                        hold_warning = " ⚠️ MANY HOLDS"
                    
                    # Вывод предсказания
                    print(f"{color}🎯 [{prediction['timestamp']}] {symbol} | Confidence: {prediction['confidence']}{hold_warning}")
                    print(f"   📊 Imbalance: {features.get('order_book_imbalance', 0):.3f} | "
                          f"Delta: {features.get('cumulative_delta', 0):.1f} | "
                          f"Volatility: {features.get('volatility', 0):.3f}%")
                    
                    # Сравнение с бейзлайном
                    from baseline_strategy import baseline_strategy
                    baseline = baseline_strategy.analyze_signal(features)
                    print(f"   🤖 Baseline: {baseline['decision']} ({baseline['confidence']:.0f}%)")
                    
                    # 🔧 ДИАГНОСТИКА: Показываем вероятности для ненулевых предсказаний
                    if prediction['prediction'] != 0 and 'probabilities' in prediction:
                        probs = prediction['probabilities']
                        if hasattr(self.model, 'classes_'):
                            prob_str = " | ".join([f"C{cls}:{p*100:.1f}%" 
                                                for cls, p in zip(self.model.classes_, probs)])
                            print(f"   📈 Probabilities: {prob_str}")
                    
                    print("-" * 60)
                else:
                    error_msg = prediction.get('error', 'Unknown error') if prediction else 'No prediction'
                    print(f"❌ Prediction failed: {error_msg}")
                    print("-" * 60)
            
            time.sleep(1)

if __name__ == "__main__":
    predictor = LivePredictor()
    predictor.start_live_predictions()
