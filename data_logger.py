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
        self.log_interval = 2  # Логируем каждые 2 секунды
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
            print("📁 Created new training_data.csv")
    
    def is_valid_features(self, features):
        """Проверяет валидность фич перед сохранением"""
        try:
            # Проверяем spread (не должен быть аномально большим)
            spread = features.get('spread_percent', 0)
            if spread > 1.0:  # spread > 1% - аномалия
                self.anomaly_count += 1
                if self.anomaly_count % 10 == 0:  # Логируем каждую 10-ю аномалию
                    print(f"🚫 Filtered anomaly: spread={spread:.4f}%")
                return False
            
            # Проверяем imbalance (должен быть между 0 и 1)
            imbalance = features.get('order_book_imbalance', 0.5)
            if imbalance < 0 or imbalance > 1:
                self.anomaly_count += 1
                if self.anomaly_count % 10 == 0:
                    print(f"🚫 Filtered anomaly: imbalance={imbalance:.4f}")
                return False
            
            # Проверяем цену (должна быть реалистичной для BTC)
            price = features.get('current_price', 0)
            if price < 1000 or price > 200000:
                self.anomaly_count += 1
                if self.anomaly_count % 10 == 0:
                    print(f"🚫 Filtered anomaly: price={price}")
                return False
            
            # Проверяем cumulative delta на разумные пределы
            delta = abs(features.get('cumulative_delta', 0))
            if delta > 10000:  # Слишком большая дельта
                self.anomaly_count += 1
                if self.anomaly_count % 10 == 0:
                    print(f"🚫 Filtered anomaly: delta={delta}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def log_features(self, features):
        """Логирует ВСЕ валидные данные (включая target=0)"""
        try:
            current_time = time.time()
            
            # Проверяем валидность данных
            if not self.is_valid_features(features):
                return
            
            # Логируем каждые 2 секунды ВСЕ валидные данные
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
                if target_val == 1:
                    target_symbol = "🟢"  # GREEN для LONG
                elif target_val == -1:
                    target_symbol = "🔴"  # RED для SHORT
                else:
                    target_symbol = "⚪"  # WHITE для HOLD
                
                # Более информативное логирование
                imbalance = features.get('order_book_imbalance', 0.5)
                spread = features.get('spread_percent', 0)
                delta = features.get('cumulative_delta', 0)
                
                print(f"💾 {target_symbol} SAVED #{self.logged_count}: "
                      f"target={target_val}, imb={imbalance:.3f}, "
                      f"spr={spread:.4f}%, delta={delta:.2f}")
                
        except Exception as e:
            print(f"❌ Data logging error: {e}")
    
    def get_stats(self):
        """Возвращает статистику по сохраненным данным"""
        try:
            if not os.path.exists(self.data_file):
                return {'total': 0, 'target_distribution': {}}
            
            total_records = 0
            target_dist = {-1: 0, 0: 0, 1: 0}
            
            with open(self.data_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_records += 1
                    if 'target' in row and row['target'].strip():
                        try:
                            target_val = int(row['target'])
                            if target_val in [-1, 0, 1]:
                                target_dist[target_val] += 1
                        except ValueError:
                            pass
            
            return {
                'total': total_records,
                'target_distribution': target_dist,
                'anomalies_filtered': self.anomaly_count
            }
            
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return {'total': 0, 'target_distribution': {}}
    
    def print_stats(self):
        """Выводит статистику сохраненных данных"""
        stats = self.get_stats()
        print(f"\n📊 DATA STATS: Total={stats['total']}, "
              f"Targets={stats['target_distribution']}, "
              f"Anomalies filtered={stats['anomalies_filtered']}")

# Глобальный экземпляр
data_logger = DataLogger()
