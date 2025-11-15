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
        
        # Используем конфигурацию для интервалов
        self.log_interval = config.data.LOG_INTERVAL
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
        """Настраивает файлы данных с улучшенной структурой"""
        os.makedirs("data", exist_ok=True)
        
        # Основной файл для обучения
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
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
                    'volatility',
                    'target',
                    'data_quality'
                ])
            print("📁 Создан новый файл данных для обучения")
        
        # Файл для сырых данных (бэкап)
        if not os.path.exists(self.raw_data_file):
            with open(self.raw_data_file, 'w', newline='', encoding='utf-8') as f:
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
                    'volatility',
                    'target',
                    'log_type'
                ])
            print("📁 Создан файл для сырых данных")
    
    def safe_csv_value(self, value):
        """🔧 БЕЗОПАСНОЕ экранирование значений для CSV"""
        if value is None:
            return ''
        str_value = str(value)
        # Экранируем запятые, переносы строк и кавычки
        if ',' in str_value or '\n' in str_value or '\r' in str_value or '"' in str_value:
            return '"' + str_value.replace('"', '""') + '"'
        return str_value
    
    def is_valid_features(self, features):
        """🔧 УМЯГЧЕННАЯ проверка валидности фич"""
        try:
            self.data_quality_stats['total_attempted'] += 1
            
            # Проверяем наличие обязательных полей
            required_fields = ['order_book_imbalance', 'spread_percent', 'current_price']
            for field in required_fields:
                if field not in features:
                    if self.data_quality_stats['total_attempted'] <= 5:
                        print(f"❌ Отсутствует поле: {field}")
                    return False
            
            # 🔧 УМЯГЧЕННЫЕ ПРОВЕРКИ ДИАПАЗОНОВ
            
            spread = features.get('spread_percent', 0)
            if spread > 5.0 or spread < 0:  # 🔧 Увеличил с 1.0 до 5.0
                if self.data_quality_stats['total_attempted'] <= 5:
                    print(f"❌ Невалидный спред: {spread}")
                return False
            
            imbalance = features.get('order_book_imbalance', 0.5)
            if imbalance < 0.01 or imbalance > 0.99:  # 🔧 Расширил диапазон
                if self.data_quality_stats['total_attempted'] <= 5:
                    print(f"❌ Невалидный imbalance: {imbalance}")
                return False
            
            price = features.get('current_price', 0)
            if price < 5000 or price > 200000:  # 🔧 Расширил диапазон
                if self.data_quality_stats['total_attempted'] <= 5:
                    print(f"❌ Невалидная цена: {price}")
                return False
            
            delta = abs(features.get('cumulative_delta', 0))
            if delta > 100000:  # 🔧 Увеличил лимит
                if self.data_quality_stats['total_attempted'] <= 5:
                    print(f"❌ Слишком большая дельта: {delta}")
                return False
            
            volatility = features.get('volatility', 0)
            if volatility < 0 or volatility > 50:  # 🔧 Увеличил лимит
                if self.data_quality_stats['total_attempted'] <= 5:
                    print(f"❌ Невалидная волатильность: {volatility}")
                return False
            
            # 🔧 ДОБАВИЛ ДЕБАГ ДЛЯ ПОНИМАНИЯ ПРОБЛЕМ
            if self.data_quality_stats['total_attempted'] <= 3:
                print(f"🔍 ДЕБАГ фич #{self.data_quality_stats['total_attempted']}:")
                print(f"   price: {price}, spread: {spread}, imbalance: {imbalance}")
                print(f"   delta: {delta}, volatility: {volatility}")
            
            return True
            
        except Exception as e:
            if self.data_quality_stats['total_attempted'] <= 5:
                print(f"❌ Ошибка проверки фич: {e}")
            return False
    
    def is_noisy_data(self, features):
        """🔧 УМЯГЧЕННАЯ проверка на зашумленность"""
        try:
            # 🔧 ВРЕМЕННО ОТКЛЮЧИМ СЛИШКОМ СТРОГУЮ ПРОВЕРКУ
            price = features.get('current_price', 0)
            spread = features.get('spread_percent', 0)
            
            # Только самые критические проверки
            if price <= 0:
                return True
                
            if spread > 10.0:  # 🔧 Увеличил порог
                return True
                
            return False
            
        except Exception as e:
            return True
    
    def calculate_data_quality_score(self, features):
        """Рассчитывает оценку качества данных"""
        score = 100  # Начальная оценка
        
        try:
            # 🔧 УМЯГЧЕННЫЕ ШТРАФЫ
            spread = features.get('spread_percent', 0)
            if spread > 0.1:
                score -= 10
            elif spread > 0.05:
                score -= 5
                
            imbalance = features.get('order_book_imbalance', 0.5)
            if imbalance < 0.3 or imbalance > 0.7:
                score -= 10
                
            volatility = features.get('volatility', 0)
            if volatility > 5.0:
                score -= 10
                
            # Бонус за хорошие данные
            if 0.4 <= imbalance <= 0.6 and spread < 0.02:
                score += 15
                
            return max(0, min(100, score))
            
        except Exception as e:
            return 50  # 🔧 Средняя оценка при ошибке
    
    def log_raw_data(self, features):
        """Логирует сырые данные для бэкапа с защитой CSV"""
        try:
            # 🔧 БЕЗОПАСНАЯ подготовка данных
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
        except Exception as e:
            print(f"❌ Ошибка логирования сырых данных: {e}")
    
    def repair_data_file(self):
        """🔧 ВОССТАНАВЛИВАЕТ поврежденный CSV файл"""
        try:
            if not os.path.exists(self.data_file):
                return True
                
            # Проверяем только каждые 100 записей чтобы не замедлять работу
            if self.logged_count % 100 != 0:
                return True
                
            print("🔧 Проверяем целостность файла данных...")
            
            # Пробуем загрузить файл
            try:
                df = pd.read_csv(self.data_file)
                print(f"✅ Файл в порядке, записей: {len(df)}")
                return True
            except Exception as e:
                print(f"⚠️ Файл поврежден, восстанавливаем...")
                
            # Создаем backup поврежденного файла
            backup_file = f"{self.data_file}.backup_{int(time.time())}"
            os.rename(self.data_file, backup_file)
            print(f"📁 Создан backup: {backup_file}")
            
            # Читаем построчно и фильтруем корректные строки
            good_rows = []
            with open(backup_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)  # Читаем заголовки
                    good_rows.append(headers)
                    
                    for i, row in enumerate(reader, start=2):
                        if len(row) == len(headers):
                            good_rows.append(row)
                        else:
                            print(f"⚠️ Пропущена строка {i}: неверное количество полей")
                except StopIteration:
                    print("⚠️ Файл пустой")
            
            # Записываем исправленный файл
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(good_rows)
            
            print(f"✅ Файл восстановлен! Сохранено {len(good_rows)-1} записей")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка восстановления файла: {e}")
            return False
    
    def log_features(self, features):
        """Улучшенное логирование фич с защитой от повреждения CSV"""
        try:
            current_time = time.time()
            
            # 🔧 ПЕРИОДИЧЕСКАЯ ПРОВЕРКА ЦЕЛОСТНОСТИ ФАЙЛА
            if self.logged_count % 100 == 0:
                self.repair_data_file()
            
            # Всегда логируем сырые данные
            self.log_raw_data(features)
            
            # Пропускаем невалидные данные
            if not self.is_valid_features(features):
                self.data_quality_stats['anomalies_detected'] += 1
                return
            
            # Контроль частоты логирования
            if current_time - self.last_log_time < self.log_interval:
                return
                
            self.last_log_time = current_time
            self.logged_count += 1
            self.data_quality_stats['successful_logs'] += 1
            
            # Расчет качества данных
            quality_score = self.calculate_data_quality_score(features)
            
            # 🔧 БЕЗОПАСНАЯ подготовка данных для CSV
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
                self.safe_csv_value(quality_score)
            ]
            
            # Проверяем что количество полей соответствует заголовкам
            expected_columns = 12
            if len(row_data) != expected_columns:
                print(f"❌ Ошибка: неверное количество полей {len(row_data)} != {expected_columns}")
                return
            
            # Логируем в основной файл
            with open(self.data_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data)
            
            # Периодическая очистка старых данных
            if self.logged_count % 100 == 0:
                self.cleanup_old_data()
            
            # Визуализация логирования
            target_val = features.get('target', 0)
            if target_val != 0:
                if target_val == 1:
                    target_symbol = "🟢"
                    target_text = "LONG"
                elif target_val == -1:
                    target_symbol = "🔴" 
                    target_text = "SHORT"
                else:
                    target_symbol = "⚪"
                    target_text = "HOLD"
                
                # Показываем детали только для ненулевых target
                imbalance = features.get('order_book_imbalance', 0)
                delta = features.get('cumulative_delta', 0)
                print(f"💾 {target_symbol} SAVED #{self.logged_count}: "
                      f"target={target_text} | "
                      f"imbalance={imbalance:.3f} | "
                      f"delta={delta:.1f} | "
                      f"quality={quality_score}%")
            else:
                # Для нулевых target показываем реже
                if self.logged_count % 20 == 0:
                    print(f"💾 ⚪ SAVED #{self.logged_count}: "
                          f"HOLD record | quality={quality_score}%")
            
            # Периодическая проверка качества данных
            if current_time - self.last_data_quality_check > 60:
                self.last_data_quality_check = current_time
                self.print_data_quality_report()
                
        except Exception as e:
            print(f"❌ Ошибка логирования: {e}")
    
    def print_data_quality_report(self):
        """Печатает отчет о качестве данных"""
        try:
            total_attempted = self.data_quality_stats['total_attempted']
            successful_logs = self.data_quality_stats['successful_logs']
            anomalies_detected = self.data_quality_stats['anomalies_detected']
            
            if total_attempted > 0:
                success_rate = (successful_logs / total_attempted) * 100
                anomaly_rate = (anomalies_detected / total_attempted) * 100
                
                print(f"\n📊 QUALITY REPORT: "
                      f"Success: {success_rate:.1f}% | "
                      f"Anomalies: {anomaly_rate:.1f}% | "
                      f"Total: {total_attempted}")
            else:
                print(f"\n📊 QUALITY REPORT: No data collected yet")
                  
        except Exception as e:
            print(f"❌ Ошибка отчета качества: {e}")
    
    def get_data_stats(self):
        """Возвращает статистику собранных данных"""
        try:
            if not os.path.exists(self.data_file):
                return {'total_records': 0, 'labeled_records': 0}
            
            # 🔧 БЕЗОПАСНАЯ загрузка CSV
            try:
                df = pd.read_csv(self.data_file)
            except:
                # Если файл поврежден, восстанавливаем
                if self.repair_data_file():
                    try:
                        df = pd.read_csv(self.data_file)
                    except:
                        return {'total_records': 0, 'labeled_records': 0}
                else:
                    return {'total_records': 0, 'labeled_records': 0}
            
            total_records = len(df)
            
            # Считаем размеченные записи (ненулевой target)
            if 'target' in df.columns:
                labeled_records = len(df[df['target'] != 0])
            else:
                labeled_records = 0
                
            return {
                'total_records': total_records,
                'labeled_records': labeled_records,
                'data_quality_avg': df['data_quality'].mean() if 'data_quality' in df.columns else 0
            }
            
        except Exception as e:
            return {'total_records': 0, 'labeled_records': 0}
    
    def cleanup_old_data(self):
        """Очистка старых данных с использованием конфига"""
        try:
            if not os.path.exists(self.data_file):
                return
                
            # 🔧 БЕЗОПАСНАЯ загрузка
            try:
                df = pd.read_csv(self.data_file)
            except:
                if self.repair_data_file():
                    try:
                        df = pd.read_csv(self.data_file)
                    except:
                        return
                else:
                    return
            
            # Используем максимальное количество записей из конфига
            if len(df) > self.max_records:
                # Оставляем только последние записи
                df = df.tail(self.max_records)
                df.to_csv(self.data_file, index=False)
                print(f"🧹 Очищены старые данные. Оставлено {len(df)} записей (максимум: {self.max_records})")
                
        except Exception as e:
            print(f"❌ Ошибка очистки данных: {e}")

# Глобальный экземпляр
data_logger = DataLogger()
