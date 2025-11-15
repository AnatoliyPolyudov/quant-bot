# data_logger.py
import csv
import os
import time

class DataLogger:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.setup_data_file()
        self.log_count = 0
    
    def setup_data_file(self):
        """Создает файл данных"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'order_book_imbalance', 'spread_percent', 
                    'cumulative_delta', 'funding_rate', 'buy_trades', 
                    'sell_trades', 'total_trades', 'current_price', 'target'
                ])
            print("📁 Created new training_data.csv")
    
    def log_features(self, features):
        """СОХРАНЯЕТ КАЖДЫЙ target НЕМЕДЛЕННО"""
        try:
            target_val = features.get('target', 0)
            if target_val != 0:
                self.log_count += 1
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
                        target_val
                    ])
                print(f"💾 SAVED #{self.log_count}: target={target_val}")
        except Exception as e:
            print(f"❌ LOG ERROR: {e}")

# Глобальный экземпляр
data_logger = DataLogger()
