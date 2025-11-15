# data_logger.py
import csv
import os
import time
from datetime import datetime
import pandas as pd
from config import config

class DataLogger:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.raw_data_file = "data/raw_data_backup.csv"
        self.setup_data_files()
        self.logged_count = 0
        self.last_log_time = 0
        
        # 🔧 ОЧЕНЬ КОРОТКИЙ ИНТЕРВАЛ
        self.log_interval = 2  # Всего 2 секунды!
        
        self.max_records = config.data.MAX_RECORDS
        
        self.anomaly_count = 0
        self.last_data_quality_check = 0
        self.data_quality_stats = {
            'total_attempted': 0,
            'successful_logs': 0,
            'anomalies_detected': 0,
            'last_quality_report': 0
        }
        
    def setup_data_files(self):
        """Настраивает файлы данных"""
        os.makedirs("data", exist_ok=True)
        
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'order_book_imbalance', 'spread_percent',
                    'cumulative_delta', 'funding_rate', 'buy_trades',
                    'sell_trades', 'total_trades', 'current_price',
                    'volatility', 'target', 'data_quality'
                ])
            print("📁 Создан новый файл данных для обучения")
        
        if not os.path.exists(self.raw_data_file):
            with open(self.raw_data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'order_book_imbalance', 'spread_percent',
                    'cumulative_delta', 'funding_rate', 'buy_trades',
                    'sell_trades', 'total_trades', 'current_price',
                    'volatility', 'target', 'log_type'
                ])
            print("📁 Создан файл для сырых данных")
    
    def safe_csv_value(self, value):
        """Безопасное экранирование для CSV"""
        if value is None:
            return ''
        str_value = str(value)
        if ',' in str_value or '\n' in str_value or '\r' in str_value or '"' in str_value:
            return '"' + str_value.replace('"', '""') + '"'
        return str_value
    
    def is_valid_features(self, features):
        """🔧 СУПЕР-МЯГКАЯ проверка - сохраняем ВСЕ"""
        try:
            self.data_quality_stats['total_attempted'] += 1
            
            # 🔧 ТОЛЬКО САМЫЕ КРИТИЧЕСКИЕ ПРОВЕРКИ
            price = features.get('current_price', 0)
            if price <= 0 or price > 500000:
                return False
                
            # 🔧 ВСЕ ОСТАЛЬНОЕ ПРИНИМАЕМ БЕЗ ПРОВЕРОК
            
            # Показываем прогресс
            if self.data_quality_stats['total_attempted'] <= 10:
                print(f"💾 ACCEPTING #{self.data_quality_stats['total_attempted']}: price={price}")
            
            return True  # 🔧 ПРИНИМАЕМ ВСЕ!
            
        except Exception as e:
            return False
    
    def is_noisy_data(self, features):
        """🔧 ОЧЕНЬ МЯГКАЯ проверка на шум"""
        try:
            price = features.get('current_price', 0)
            return price <= 0  # 🔧 Только полный крах
        except:
            return False
    
    def calculate_data_quality_score(self, features):
        """Простая оценка качества"""
        return 80  # 🔧 Всегда высокая оценка
    
    def log_raw_data(self, features):
        """Логируем сырые данные"""
        try:
            row_data = [
                self.safe_csv_value(features.get('timestamp', '')),
                self.safe_csv_value(features.get('order_book_imbalance', 0)),
                self.safe_csv_value(features.get('spread_percent', 0)),
                self.safe_csv_value(features.get('cumulative_delta', 0)),
                self.safe_csv_value(features.get('funding_rate', 0)),
                self.safe_csv_value(features.get('buy_trades', 0)),
                self.safe_csv_value(features.get('sell_trades', 0)),
                self.safe_csv_value(features.get('total_trades', 0)),
                self.safe_csv_value(features.get('current_price', 0)),
                self.safe_csv_value(features.get('volatility', 0)),
                self.safe_csv_value(features.get('target', 0)),
                'raw'
            ]
            
            with open(self.raw_data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
        except:
            pass
    
    def log_features(self, features):
        """Основное логирование"""
        try:
            current_time = time.time()
            
            # Всегда логируем сырые данные
            self.log_raw_data(features)
            
            # 🔧 МЯГКАЯ ВАЛИДАЦИЯ
            if not self.is_valid_features(features):
                self.data_quality_stats['anomalies_detected'] += 1
                return
            
            # 🔧 ЧАСТОЕ ЛОГИРОВАНИЕ (2 секунды)
            if current_time - self.last_log_time < self.log_interval:
                return
                
            self.last_log_time = current_time
            self.logged_count += 1
            self.data_quality_stats['successful_logs'] += 1
            
            # Подготовка данных
            row_data = [
                self.safe_csv_value(features.get('timestamp', '')),
                self.safe_csv_value(features.get('order_book_imbalance', 0)),
                self.safe_csv_value(features.get('spread_percent', 0)),
                self.safe_csv_value(features.get('cumulative_delta', 0)),
                self.safe_csv_value(features.get('funding_rate', 0)),
                self.safe_csv_value(features.get('buy_trades', 0)),
                self.safe_csv_value(features.get('sell_trades', 0)),
                self.safe_csv_value(features.get('total_trades', 0)),
                self.safe_csv_value(features.get('current_price', 0)),
                self.safe_csv_value(features.get('volatility', 0)),
                self.safe_csv_value(features.get('target', 0)),
                self.safe_csv_value(80)  # Всегда высокое качество
            ]
            
            # Сохраняем в основной файл
            with open(self.data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            
            # Визуализация
            target_val = features.get('target', 0)
            if target_val != 0:
                symbol = "🟢" if target_val == 1 else "🔴"
                text = "LONG" if target_val == 1 else "SHORT"
                print(f"💾 {symbol} SAVED #{self.logged_count}: target={text}")
            elif self.logged_count % 10 == 0:
                print(f"💾 ⚪ SAVED #{self.logged_count}: HOLD record")
                
        except Exception as e:
            print(f"❌ Ошибка логирования: {e}")

# Глобальный экземпляр
data_logger = DataLogger()
