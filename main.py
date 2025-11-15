# main.py
from data_collector import data_collector
from data_monitor import DataMonitor
from live_predictor import LivePredictor
import time
import argparse
import sys
import os
from datetime import datetime

class QuantumBot:
    def __init__(self):
        self.monitor = DataMonitor()
        self.predictor = None
        self.operation_mode = "DATA_COLLECTION"  # DATA_COLLECTION, TRADING, MONITORING
        self.start_time = datetime.now()
        self.performance_stats = {
            'uptime': 0,
            'data_points_collected': 0,
            'predictions_made': 0,
            'last_health_check': 0
        }
        
    def print_banner(self):
        """Печатает баннер при запуске"""
        print("\n" + "="*70)
        print("🚀 QUANTUM TRADING BOT v2.0")
        print("="*70)
        print("📊 Режимы работы:")
        print("   • DATA_COLLECTION - Сбор и разметка данных")
        print("   • TRADING - Торговля с ML предсказаниями") 
        print("   • MONITORING - Мониторинг без торговли")
        print("="*70)
        
    def parse_arguments(self):
        """Парсит аргументы командной строки"""
        parser = argparse.ArgumentParser(description='Quantum Trading Bot')
        parser.add_argument('--mode', type=str, default='data', 
                          choices=['data', 'trade', 'monitor', 'predict'],
                          help='Режим работы: data (сбор данных), trade (торговля), monitor (мониторинг), predict (предсказания)')
        parser.add_argument('--model', type=str, default='models/quant_model.pkl',
                          help='Путь к файлу модели')
        parser.add_argument('--symbol', type=str, default='BTC-USDT-SWAP',
                          help='Торговая пара')
        parser.add_argument('--verbose', action='store_true',
                          help='Подробный вывод')
        
        return parser.parse_args()
    
    def setup_operation_mode(self, mode):
        """Настраивает режим работы"""
        mode_map = {
            'data': 'DATA_COLLECTION',
            'trade': 'TRADING', 
            'monitor': 'MONITORING',
            'predict': 'PREDICTION'
        }
        
        self.operation_mode = mode_map.get(mode, 'DATA_COLLECTION')
        
        print(f"\n🎯 УСТАНОВЛЕН РЕЖИМ: {self.operation_mode}")
        
        if self.operation_mode == 'TRADING':
            print("💰 РЕЖИМ ТОРГОВЛИ: Бот будет делать предсказания и торговать")
            self.predictor = LivePredictor()
        elif self.operation_mode == 'PREDICTION':
            print("🔮 РЕЖИМ ПРЕДСКАЗАНИЙ: Только предсказания без торговли")
            self.predictor = LivePredictor()
        elif self.operation_mode == 'MONITORING':
            print("📊 РЕЖИМ МОНИТОРИНГА: Сбор данных и анализ без торговли")
        else:
            print("📈 РЕЖИМ СБОРА ДАННЫХ: Активный сбор и разметка данных")
    
    def check_system_health(self):
        """Проверяет здоровье системы"""
        current_time = time.time()
        
        # Проверяем не чаще чем раз в 60 секунд
        if current_time - self.performance_stats['last_health_check'] < 60:
            return True
            
        self.performance_stats['last_health_check'] = current_time
        self.performance_stats['uptime'] = (datetime.now() - self.start_time).total_seconds()
        
        issues = []
        
        # Проверяем сбор данных
        try:
            conn_stats = data_collector.get_connection_stats()
            if conn_stats['connection_quality'] in ['POOR', 'DISCONNECTED']:
                issues.append(f"Плохое качество соединения: {conn_stats['connection_quality']}")
                
            if conn_stats['data_quality_issues'] > 10:
                issues.append(f"Много проблем с качеством данных: {conn_stats['data_quality_issues']}")
                
        except Exception as e:
            issues.append(f"Ошибка проверки сборщика данных: {e}")
        
        # Проверяем модель в режиме торговли
        if self.operation_mode in ['TRADING', 'PREDICTION'] and self.predictor:
            try:
                health_status = self.predictor.check_model_health()
                if "❌" in health_status:
                    issues.append(f"Проблемы с моделью: {health_status}")
            except Exception as e:
                issues.append(f"Ошибка проверки модели: {e}")
        
        # Выводим отчет о здоровье
        if issues:
            print(f"\n⚠️  ПРОБЛЕМЫ СИСТЕМЫ:")
            for issue in issues:
                print(f"   • {issue}")
            return False
        else:
            if current_time % 300 < 60:  # Каждые 5 минут
                print(f"\n✅ СИСТЕМА В НОРМЕ (аптайм: {self.performance_stats['uptime']:.0f}с)")
            return True
    
    def run_data_collection_mode(self):
        """Запускает режим сбора данных"""
        print("\n📈 ЗАПУСК СБОРА ДАННЫХ...")
        print("💡 Собираем данные для обучения ML модели")
        print("💡 Данные автоматически размечаются каждые 8 секунд")
        print("💡 Для остановки нажмите Ctrl+C\n")
        
        last_progress_check = 0
        last_health_check = 0
        
        try:
            while True:
                current_time = time.time()
                
                # Показываем прогресс каждые 2 минуты
                if current_time - last_progress_check > 120:
                    self.monitor.print_progress_report()
                    last_progress_check = current_time
                
                # Проверяем здоровье системы каждую минуту
                if current_time - last_health_check > 60:
                    self.check_system_health()
                    last_health_check = current_time
                
                # Проверяем готовность данных для обучения
                readiness = self.monitor.check_model_readiness()
                if readiness['is_ready'] and current_time % 300 < 60:  # Каждые 5 минут
                    print("\n🎉 ДАННЫЕ ГОТОВЫ ДЛЯ ОБУЧЕНИЯ!")
                    print("💡 Запустите: python train_model.py")
                    print("💡 Или перезапустите бота с режимом --mode=predict\n")
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n🛑 Сбор данных остановлен")
    
    def run_prediction_mode(self):
        """Запускает режим предсказаний"""
        print("\n🔮 ЗАПУСК РЕЖИМА ПРЕДСКАЗАНИЙ...")
        print("💡 ML модель делает предсказания в реальном времени")
        print("💡 Сравниваем с baseline стратегией")
        print("💡 Для остановки нажмите Ctrl+C\n")
        
        if not self.predictor or self.predictor.model is None:
            print("❌ Модель не загружена! Сначала обучите модель:")
            print("   python train_model.py")
            return
        
        # Показываем стартовую информацию
        progress = self.monitor.check_data_progress()
        print(f"📊 Используется модель обученная на {progress['labeled_records']} записях")
        print(f"🎯 Качество данных: {progress['data_quality']}\n")
        
        try:
            self.predictor.start_live_predictions()
        except KeyboardInterrupt:
            print("\n🛑 Предсказания остановлены")
    
    def run_trading_mode(self):
        """Запускает режим торговли"""
        print("\n💰 ЗАПУСК РЕЖИМА ТОРГОВЛИ...")
        print("⚠️  ВНИМАНИЕ: Это экспериментальный режим!")
        print("💡 Бот будет делать предсказания и торговать")
        print("💡 Используйте на свой страх и риск!")
        print("💡 Для остановки нажмите Ctrl+C\n")
        
        # Подтверждение пользователя
        response = input("🔒 Подтвердите запуск торговли (введите 'YES' для продолжения): ")
        if response != 'YES':
            print("🛑 Торговля отменена")
            return
        
        if not self.predictor or self.predictor.model is None:
            print("❌ Модель не загружена! Сначала обучите модель:")
            print("   python train_model.py")
            return
        
        print("🚀 ЗАПУСК ТОРГОВЛИ...")
        # Здесь будет интеграция с торговым API
        print("📈 Торговая логика будет реализована в будущих версиях")
        print("💡 Пока что используйте режим --mode=predict для тестирования\n")
        
        try:
            while True:
                # Временная заглушка для торговой логики
                time.sleep(10)
                print("🔧 Торговая логика в разработке...")
        except KeyboardInterrupt:
            print("\n🛑 Торговля остановлена")
    
    def run_monitoring_mode(self):
        """Запускает режим мониторинга"""
        print("\n📊 ЗАПУСК РЕЖИМА МОНИТОРИНГА...")
        print("💡 Мониторинг данных и системы без активных действий")
        print("💡 Для остановки нажмите Ctrl+C\n")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Расширенный мониторинг каждые 30 секунд
                self.monitor.print_progress_report()
                
                # Дополнительная информация каждые 5 итераций
                if iteration % 5 == 0:
                    print("\n🔧 СИСТЕМНАЯ ИНФОРМАЦИЯ:")
                    conn_stats = data_collector.get_connection_stats()
                    print(f"   📡 Сообщений: {conn_stats['messages_received']}")
                    print(f"   📊 Фич обработано: {conn_stats['features_processed']}")
                    print(f"   🔗 Качество связи: {conn_stats['connection_quality']}")
                    print(f"   ⏱️  Аптайм: {self.performance_stats['uptime']:.0f}с")
                
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен")
    
    def run(self):
        """Главный метод запуска бота"""
        args = self.parse_arguments()
        
        self.print_banner()
        self.setup_operation_mode(args.mode)
        
        # Запускаем сбор данных в любом режиме
        print("\n🔌 Подключаемся к бирже...")
        data_collector.start()
        
        # Ждем подключения
        time.sleep(3)
        
        # Запускаем выбранный режим
        if self.operation_mode == 'TRADING':
            self.run_trading_mode()
        elif self.operation_mode == 'PREDICTION':
            self.run_prediction_mode()
        elif self.operation_mode == 'MONITORING':
            self.run_monitoring_mode()
        else:
            self.run_data_collection_mode()
    
    def cleanup(self):
        """Очистка ресурсов при завершении"""
        print("\n🧹 Завершение работы...")
        if hasattr(data_collector, 'ws'):
            data_collector.ws.close()
        print("✅ Бот остановлен")

def main():
    bot = QuantumBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Прерывание пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()
