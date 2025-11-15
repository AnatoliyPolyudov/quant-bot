# data_monitor.py
import pandas as pd
import os
from datetime import datetime
import time

class DataMonitor:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        
    def check_data_progress(self):
        """Проверяет прогресс сбора данных"""
        if not os.path.exists(self.data_file):
            return {
                'total_records': 0,
                'labeled_records': 0,
                'target_distribution': {},
                'data_quality': 'NO_DATA'
            }
        
        try:
            df = pd.read_csv(self.data_file)
            total_records = len(df)
            
            # Проверяем размеченные данные
            if 'target' in df.columns:
                labeled_df = df.dropna(subset=['target'])
                labeled_records = len(labeled_df)
                
                # Распределение target
                target_dist = labeled_df['target'].value_counts().to_dict()
                
                # Качество данных
                if labeled_records == 0:
                    quality = 'COLLECTING'  # данные есть, но target еще не рассчитан
                elif labeled_records < 50:
                    quality = 'MINIMAL'
                elif labeled_records < 200:
                    quality = 'GOOD' 
                else:
                    quality = 'EXCELLENT'
            else:
                labeled_records = 0
                target_dist = {}
                quality = 'NO_TARGET'
            
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
        elif progress['data_quality'] == 'NO_TARGET':
            print("💡 Рекомендация: Ожидайте расчета target (5+ минут)")
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
            time.sleep(30)  # Обновление каждые 30 секунд
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен")

if __name__ == "__main__":
    monitor_continuous()
