# data_monitor.py
import os
import csv
from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np

class DataMonitor:
    def __init__(self):
        self.data_file = "data/training_data.csv"
        self.raw_data_file = "data/raw_data_backup.csv"
        self.last_check_time = 0
        self.check_interval = 30  # 🔧 Проверка каждые 30 секунд
        
    def check_data_progress(self):
        """Проверяет прогресс сбора данных с улучшенной аналитикой"""
        if not os.path.exists(self.data_file):
            return {
                'total_records': 0,
                'labeled_records': 0,
                'target_distribution': {},
                'data_quality': 'NO_DATA',
                'data_quality_score': 0,
                'recent_activity': 'NO_ACTIVITY'
            }
        
        try:
            df = pd.read_csv(self.data_file)
            total_records = len(df)
            
            # 🔧 НОВОЕ: Проверяем наличие колонки target
            if 'target' not in df.columns:
                return {
                    'total_records': total_records,
                    'labeled_records': 0,
                    'target_distribution': {},
                    'data_quality': 'NO_TARGET',
                    'data_quality_score': 0,
                    'recent_activity': 'COLLECTING'
                }
            
            # Размеченные записи (ненулевой target)
            labeled_mask = df['target'].notna() & (df['target'] != 0)
            labeled_records = len(df[labeled_mask])
            
            # 🔧 НОВОЕ: Распределение target с процентами
            target_dist = {}
            if labeled_records > 0:
                target_counts = df[labeled_mask]['target'].value_counts()
                for target_val, count in target_counts.items():
                    percentage = (count / labeled_records) * 100
                    target_dist[int(target_val)] = {
                        'count': count,
                        'percentage': percentage
                    }
            
            # 🔧 НОВОЕ: Оценка качества данных
            quality_score = self.calculate_data_quality(df)
            
            # 🔧 НОВОЕ: Активность сбора данных
            recent_activity = self.check_recent_activity(df)
            
            # Общее качество данных
            if labeled_records == 0 and total_records > 0:
                quality = 'COLLECTING'
            elif labeled_records < 50:
                quality = 'MINIMAL'
            elif labeled_records < 200:
                quality = 'GOOD'
            else:
                quality = 'EXCELLENT'
                
            return {
                'total_records': total_records,
                'labeled_records': labeled_records,
                'target_distribution': target_dist,
                'data_quality': quality,
                'data_quality_score': quality_score,
                'recent_activity': recent_activity,
                'feature_stats': self.get_feature_stats(df)
            }
            
        except Exception as e:
            print(f"❌ Ошибка анализа данных: {e}")
            return {
                'total_records': 0,
                'labeled_records': 0,
                'target_distribution': {},
                'data_quality': 'ERROR',
                'data_quality_score': 0,
                'recent_activity': 'ERROR'
            }
    
    def calculate_data_quality(self, df):
        """🔧 НОВОЕ: Рассчитывает общий показатель качества данных"""
        try:
            score = 0
            max_score = 100
            
            # Наличие данных
            if len(df) > 0:
                score += 20
            
            # Наличие размеченных данных
            if 'target' in df.columns:
                labeled_count = len(df[df['target'].notna() & (df['target'] != 0)])
                if labeled_count > 0:
                    score += 30
                    # Бонус за баланс классов
                    if labeled_count >= 50:
                        target_counts = df[df['target'] != 0]['target'].value_counts()
                        if len(target_counts) >= 2:
                            balance_score = min(target_counts) / max(target_counts) * 20
                            score += balance_score
            
            # Качество фич
            feature_quality = self.assess_feature_quality(df)
            score += feature_quality
            
            return min(max_score, score)
            
        except Exception as e:
            return 0
    
    def assess_feature_quality(self, df):
        """🔧 НОВОЕ: Оценивает качество отдельных фич"""
        score = 0
        important_features = ['order_book_imbalance', 'spread_percent', 'cumulative_delta']
        
        for feature in important_features:
            if feature in df.columns:
                # Проверяем на наличие NaN
                nan_ratio = df[feature].isna().sum() / len(df)
                if nan_ratio < 0.1:  # Меньше 10% NaN
                    score += 10
                
                # Проверяем дисперсию (не постоянные значения)
                if df[feature].nunique() > 10:
                    score += 5
        
        return min(30, score)
    
    def check_recent_activity(self, df):
        """🔧 НОВОЕ: Проверяет активность сбора данных"""
        try:
            if 'timestamp' not in df.columns or len(df) == 0:
                return 'UNKNOWN'
            
            # Конвертируем timestamp в datetime
            df['datetime'] = pd.to_datetime(df['timestamp'])
            latest_record = df['datetime'].max()
            time_diff = datetime.now() - latest_record
            
            if time_diff < timedelta(minutes=2):
                return 'ACTIVE'
            elif time_diff < timedelta(minutes=5):
                return 'SLOW'
            elif time_diff < timedelta(minutes=10):
                return 'STALLED'
            else:
                return 'INACTIVE'
                
        except Exception as e:
            return 'UNKNOWN'
    
    def get_feature_stats(self, df):
        """🔧 НОВОЕ: Статистика по фичам"""
        stats = {}
        feature_columns = ['order_book_imbalance', 'spread_percent', 'cumulative_delta', 'volatility']
        
        for feature in feature_columns:
            if feature in df.columns:
                feature_data = df[feature].dropna()
                if len(feature_data) > 0:
                    stats[feature] = {
                        'min': float(feature_data.min()),
                        'max': float(feature_data.max()),
                        'mean': float(feature_data.mean()),
                        'std': float(feature_data.std()),
                        'count': len(feature_data)
                    }
        
        return stats
    
    def get_raw_data_stats(self):
        """🔧 НОВОЕ: Статистика по сырым данным"""
        if not os.path.exists(self.raw_data_file):
            return {'total_raw_records': 0, 'raw_vs_processed': 0}
        
        try:
            raw_df = pd.read_csv(self.raw_data_file)
            processed_df = pd.read_csv(self.data_file) if os.path.exists(self.data_file) else pd.DataFrame()
            
            raw_count = len(raw_df)
            processed_count = len(processed_df) if not processed_df.empty else 0
            
            conversion_rate = (processed_count / raw_count * 100) if raw_count > 0 else 0
            
            return {
                'total_raw_records': raw_count,
                'raw_vs_processed': conversion_rate
            }
        except Exception as e:
            return {'total_raw_records': 0, 'raw_vs_processed': 0}
    
    def print_progress_report(self):
        """Выводит улучшенный отчет о прогрессе"""
        progress = self.check_data_progress()
        raw_stats = self.get_raw_data_stats()
        
        print("\n" + "="*70)
        print("📊 ПОДРОБНЫЙ ОТЧЕТ О СБОРЕ ДАННЫХ")
        print("="*70)
        
        # Основная статистика
        print(f"📁 Всего записей: {progress['total_records']}")
        print(f"🎯 Размеченных записей: {progress['labeled_records']}")
        print(f"📈 Качество данных: {progress['data_quality']} ({progress['data_quality_score']}/100)")
        print(f"🔄 Активность: {progress['recent_activity']}")
        
        # 🔧 НОВОЕ: Статистика сырых данных
        print(f"📋 Сырых данных: {raw_stats['total_raw_records']}")
        print(f"📊 Конверсия в обучающие: {raw_stats['raw_vs_processed']:.1f}%")
        
        # Распределение target
        if progress['target_distribution']:
            print(f"\n🎯 РАСПРЕДЕЛЕНИЕ TARGET:")
            for target_val, info in progress['target_distribution'].items():
                symbol = "🔴" if target_val == -1 else "🟢" if target_val == 1 else "⚪"
                print(f"   {symbol} Target {target_val}: {info['count']} записей ({info['percentage']:.1f}%)")
        
        # 🔧 НОВОЕ: Статистика фич
        if progress['feature_stats']:
            print(f"\n📈 СТАТИСТИКА ФИЧ:")
            for feature, stats in list(progress['feature_stats'].items())[:3]:  # Показываем топ-3
                print(f"   {feature}:")
                print(f"      min={stats['min']:.4f}, max={stats['max']:.4f}")
                print(f"      mean={stats['mean']:.4f} ± {stats['std']:.4f}")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        if progress['data_quality'] == 'NO_DATA':
            print("   • Запустите бота для сбора данных")
        elif progress['data_quality'] == 'COLLECTING':
            print("   • Данные собираются, target скоро появится")
        elif progress['data_quality'] == 'MINIMAL':
            records_needed = 50 - progress['labeled_records']
            print(f"   • Соберите еще {records_needed} размеченных записей для обучения")
        elif progress['data_quality'] == 'GOOD':
            print("   • Можно начинать обучение модели!")
            if progress['labeled_records'] < 200:
                print("   • Для лучшего качества соберите 200+ размеченных записей")
        elif progress['data_quality'] == 'EXCELLENT':
            print("   • Отличный объем данных! Модель должна хорошо обучиться")
        
        # 🔧 НОВОЕ: Предупреждения о качестве
        if progress['recent_activity'] in ['SLOW', 'STALLED']:
            print(f"   ⚠️  Низкая активность сбора данных: {progress['recent_activity']}")
        
        if progress['data_quality_score'] < 50:
            print(f"   ⚠️  Низкое качество данных: {progress['data_quality_score']}/100")
        
        print("="*70)
    
    def check_model_readiness(self):
        """🔧 НОВОЕ: Проверяет готовность данных для обучения модели"""
        progress = self.check_data_progress()
        
        requirements = {
            'min_labeled_records': 30,
            'min_quality_score': 40,
            'require_multiple_classes': True
        }
        
        issues = []
        
        if progress['labeled_records'] < requirements['min_labeled_records']:
            issues.append(f"Недостаточно размеченных данных: {progress['labeled_records']}/{requirements['min_labeled_records']}")
        
        if progress['data_quality_score'] < requirements['min_quality_score']:
            issues.append(f"Низкое качество данных: {progress['data_quality_score']}/{requirements['min_quality_score']}")
        
        if requirements['require_multiple_classes'] and len(progress['target_distribution']) < 2:
            issues.append("Необходимы данные как минимум для 2 классов (LONG/SHORT)")
        
        is_ready = len(issues) == 0
        
        return {
            'is_ready': is_ready,
            'issues': issues,
            'progress': progress
        }

def monitor_continuous():
    """Непрерывный мониторинг прогресса с улучшенным интерфейсом"""
    monitor = DataMonitor()
    
    print("🚀 ЗАПУСК ПРОДВИНУТОГО МОНИТОРИНГА ДАННЫХ...")
    print("💡 Мониторинг будет обновляться каждые 30 секунд")
    print("💡 Для остановки нажмите Ctrl+C\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # 🔧 НОВОЕ: Периодическая проверка готовности к обучению
            if iteration % 3 == 0:  # Каждые 3 итерации (90 секунд)
                readiness = monitor.check_model_readiness()
                if readiness['is_ready']:
                    print("\n🎉 ДАННЫЕ ГОТОВЫ ДЛЯ ОБУЧЕНИЯ МОДЕЛИ!")
                    print("💡 Запустите: python train_model.py")
                elif iteration % 6 == 0:  # Каждые 6 итераций
                    print(f"\n🔍 ПРОВЕРКА ГОТОВНОСТИ:")
                    for issue in readiness['issues']:
                        print(f"   ❌ {issue}")
            
            monitor.print_progress_report()
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен")

if __name__ == "__main__":
    monitor_continuous()
