# data_logger.py
import csv
import os
from datetime import datetime

class DataLogger:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.setup_data_file()
        self.last_log_time = 0
        self.log_interval = 30  # Логировать каждые 30 секунд
    
    def setup_data_file(self):
        """Создает файл данных с заголовками включая target"""
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'order_book_imbalance',
                    'spread_percent', 
                    'cumulative_delta',
                    'funding_rate',
                    'buy_trades',
                    'sell_trades',
                    'total_trades',
                    'current_price',
                    'target'
                ])
            print("📁 Created new training_data.csv")
    
    def log_features(self, features):
        """Сохраняет фичи в CSV КАЖДЫЕ 30 СЕКУНД"""
        try:
            current_time = time.time()
            
            # Логируем только каждые 30 секунд И если есть target
            if (current_time - self.last_log_time >= self.log_interval and 
                features.get('target', 0) != 0):
                
                self.last_log_time = current_time
                
                with open(self.data_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        features['timestamp'],
                        features['order_book_imbalance'],
                        features['spread_percent'],
                        features['cumulative_delta'],
                        features['funding_rate'],
                        features['buy_trades'],
                        features['sell_trades'],
                        features['total_trades'],
                        features['current_price'],
                        features['target']
                    ])
                print(f"💾 Data logged: target={features['target']}")
                
        except Exception as e:
            print(f"❌ Data logging error: {e}")

# Глобальный экземпляр
data_logger = DataLogger()
