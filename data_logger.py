# data_logger.py
import csv
import os
import time

class DataLogger:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.setup_data_file()
        self.logged_count = 0
        self.last_log_time = 0
        self.log_interval = 2  # Логируем каждые 2 секунды
    
    def setup_data_file(self):
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
        """Логирует ВСЕ данные (включая target=0)"""
        try:
            current_time = time.time()
            
            # Логируем каждые 2 секунды ВСЕ данные
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
                target_symbol = "🎯" if target_val != 0 else "⚪"
                print(f"💾 {target_symbol} SAVED #{self.logged_count}: target={target_val}")
                
        except Exception as e:
            print(f"❌ Data logging error: {e}")

data_logger = DataLogger()
