# data_monitor.py
import os
import csv
from datetime import datetime
import time

class DataMonitor:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        
    def check_data_progress(self):
        """Проверяет прогресс сбора данных без pandas"""
        if not os.path.exists(self.data_file):
            return {
                'total_records': 0,
                'labeled_records': 0,
                'target_distribution': {},
                'data_quality': 'NO_DATA'
            }
        
        try:
            total_records = 0
            labeled_records = 0
            target_dist = {-1: 0, 0: 0, 1: 0}
            
            with open(self.data_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_records += 1
                    
                    # Проверяем target
                    if 'target' in row and row['target'].strip():
                        try:
                            target_val = int(row['target'])
                            labeled_records += 1
                            if target_val in [-1, 0, 1]:
                                target_dist[target_val] += 1
                        except ValueError:
                            pass
            
            # Качество данных
            if labeled_records == 0 and total_records > 0:
                quality = 'COLLECTING'
            elif labeled_records < 50:
                quality = 'MINIMAL'
            elif labeled_records < 200:
                quality = 'GOOD'
            else:
                quality = 'EXCELLENT'
                
            # Убираем нулевые значения из распределения
            target_dist = {k: v for k, v in target_dist.items() if v > 0}
            
            return {
                'total_records': total_records,
                'labeled_records': labeled_records,
                'target_distribution': target_dist,
                'data_quality': quality
            }
            
        except Exception as e:
            return {
                'total_records': 0,
                'labeled_records': 0,
                'target_distribution': {},
                'data_quality': 'ERROR'
            }
    
    def print_progress_report(self):
        """Выводит отчет о прогрессе"""
        progress = self.check_data_progress()
        
        print("\n" + "="*60)
        print("📊 ОТЧЕТ О СБОРЕ ДАННЫХ")
        print("="*60)
        
        print(f"📁 Всего записей: {progress['total_records']}")
        print(f"🎯 Размеченных записей: {progress['labeled_records']}")
        print(f"📈 Качество данных: {progress['data_quality']}")
        
        if progress['target_distribution']:
            print(f"📊 Распределение target: {progress['target_distribution']}")
        
        # Рекомендации
        if progress['data_quality'] == 'NO_DATA':
            print("💡 Рекомендация: Запустите бота для сбора данных")
        elif progress['data_quality'] == 'COLLECTING':
            print("💡 Рекомендация: Данные собираются, target скоро будет")
        elif progress['data_quality'] == 'MINIMAL':
            records_needed = 50 - progress['labeled_records']
            print(f"💡 Рекомендация: Соберите еще {records_needed} записей для обучения")
        elif progress['data_quality'] == 'GOOD':
            print("💡 Рекомендация: Можно начинать обучение модели!")
        elif progress['data_quality'] == 'EXCELLENT':
            print("💡 Рекомендация: Отличный объем данных для обучения!")
        
        print("="*60)

def monitor_continuous():
    """Непрерывный мониторинг прогресса"""
    monitor = DataMonitor()
    
    print("🚀 ЗАПУСК МОНИТОРИНГА ДАННЫХ...")
    print("💡 Мониторинг будет обновляться каждые 30 секунд")
    print("💡 Для остановки нажмите Ctrl+C\n")
    
    try:
        while True:
            monitor.print_progress_report()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен")

if __name__ == "__main__":
    monitor_continuous()
