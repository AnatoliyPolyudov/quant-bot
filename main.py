# main.py
from data_collector import data_collector
import time

def main():
    print("🚀 Quantum Bot Starting...")
    
    # Запускаем сбор данных
    data_collector.start()
    
    # Главный цикл
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped")

if __name__ == "__main__":
    main()
