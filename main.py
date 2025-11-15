# main.py
from data_collector import data_collector
from data_monitor import DataMonitor
import time

def main():
    print("🚀 Quantum Bot Starting...")
    
    # Запускаем сбор данных
    data_collector.start()
    
    # Монитор прогресса
    monitor = DataMonitor()
    
    # Главный цикл
    try:
        last_progress_check = 0
        
        while True:
            current_time = time.time()
            
            # Показываем прогресс каждые 2 минуты
            if current_time - last_progress_check > 120:
                monitor.print_progress_report()
                last_progress_check = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")

if __name__ == "__main__":
    main()
