# data_logger.py
import csv
import os
import time
from datetime import datetime

class DataLogger:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.setup_data_file()
        self.logged_count = 0
        self.last_log_time = 0
        self.log_interval = 5  # 🔧 Увеличить до 5 секунд
        self.anomaly_count = 0
        
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
                    'current_price',
                    'target'
                ])
    
    def is_valid_features(self, features):
        """Проверяет валидность фич перед сохранением"""
        try:
            spread = features.get('spread_percent', 0)
            if spread > 1.0:
                return False
            
            imbalance = features.get('order_book_imbalance', 0.5)
            if imbalance < 0 or imbalance > 1:
                return False
            
            price = features.get('current_price', 0)
            if price < 1000 or price > 200000:
                return False
            
            delta = abs(features.get('cumulative_delta', 0))
            if delta > 10000:
                return False
            
            return True
            
        except Exception as e:
            return False
    
    def log_features(self, features):
        """Логирует данные с минимальным выводом"""
        try:
            current_time = time.time()
            
            if not self.is_valid_features(features):
                return
            
            # 🔧 Логируем только каждые 5 секунд
            if current_time - self.last_log_time >= self.log_interval:
                self.last_log_time = current_time
                self.logged_count += 1
                
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
                        features.get('target', 0)
                    ])
                
                target_val = features.get('target', 0)
                
                # 🔇 ЛОГИРУЕМ ТОЛЬКО target ≠ 0
                if target_val != 0:
                    if target_val == 1:
                        target_symbol = "🟢"
                    elif target_val == -1:
                        target_symbol = "🔴"
                    else:
                        target_symbol = "⚪"
                    
                    print(f"💾 {target_symbol} SAVED #{self.logged_count}: target={target_val}")
                
        except Exception as e:
            pass  # 🔇 Без вывода ошибок

# Глобальный экземпляр
data_logger = DataLogger()
