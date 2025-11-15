# data_logger.py
import json
import csv
import os
from datetime import datetime

class DataLogger:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.setup_data_file()
    
    def setup_data_file(self):
        """Создает файл данных с заголовками"""
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
                    'target'  # будем заполнять позже
                ])
    
    def log_features(self, features):
        """Сохраняет фичи в CSV"""
        try:
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
                    ''  # target пока пустой
                ])
            print(f"💾 Data logged: {features['timestamp']}")
        except Exception as e:
            print(f"❌ Data logging error: {e}")

# Глобальный экземпляр
data_logger = DataLogger()
