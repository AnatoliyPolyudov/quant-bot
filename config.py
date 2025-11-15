# config.py
from dataclasses import dataclass
from typing import List, Dict, Any
import os
from datetime import timedelta

@dataclass
class DataConfig:
    """Конфигурация сбора данных"""
    # WebSocket настройки
    WS_URL: str = "wss://ws.okx.com:8443/ws/v5/public"
    RECONNECT_ATTEMPTS: int = 10
    RECONNECT_DELAY: int = 5  # секунд
    
    # Каналы данных
    CHANNELS: List[str] = None
    
    # Символы для торговли
    SYMBOL: str = "BTC-USDT-SWAP"
    SYMBOLS: List[str] = None
    
    # Настройки фич
    FEATURE_WINDOW: int = 50
    VOLATILITY_WINDOW: int = 30
    TARGET_HORIZON: int = 8  # секунд для расчета target
    TARGET_THRESHOLD: float = 0.01  # 0.01% порог для target
    
    # Логирование данных
    LOG_INTERVAL: int = 5  # секунд между записями
    MAX_RECORDS: int = 10000  # максимальное количество записей в файле
    
    def __post_init__(self):
        if self.CHANNELS is None:
            self.CHANNELS = ["books", "trades", "tickers"]
        if self.SYMBOLS is None:
            self.SYMBOLS = [self.SYMBOL]

@dataclass
class StrategyConfig:
    """Конфигурация торговых стратегий"""
    
    # Baseline стратегия
    BASELINE_MIN_IMBALANCE: float = 0.58
    BASELINE_MIN_DELTA: float = 2
    BASELINE_MAX_SPREAD: float = 0.025
    BASELINE_MAX_VOLATILITY: float = 0.8
    BASELINE_MIN_CONFIDENCE: int = 60
    
    # Веса фич для композитного скоринга
    FEATURE_WEIGHTS: Dict[str, float] = None
    
    # Адаптивные параметры для разных рыночных режимов
    VOLATILE_MARKET_PARAMS: Dict[str, Any] = None
    TRENDING_MARKET_PARAMS: Dict[str, Any] = None
    NORMAL_MARKET_PARAMS: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.FEATURE_WEIGHTS is None:
            self.FEATURE_WEIGHTS = {
                'imbalance': 0.35,
                'delta': 0.25,
                'spread': 0.15,
                'volatility': 0.15,
                'funding': 0.10
            }
        
        if self.VOLATILE_MARKET_PARAMS is None:
            self.VOLATILE_MARKET_PARAMS = {
                'min_imbalance': 0.62,
                'min_delta': 3,
                'max_volatility': 0.6
            }
        
        if self.TRENDING_MARKET_PARAMS is None:
            self.TRENDING_MARKET_PARAMS = {
                'min_imbalance': 0.56,
                'min_delta': 1,
                'max_volatility': 1.0
            }
        
        if self.NORMAL_MARKET_PARAMS is None:
            self.NORMAL_MARKET_PARAMS = {
                'min_imbalance': 0.58,
                'min_delta': 2,
                'max_volatility': 0.8
            }

@dataclass
class ModelConfig:
    """Конфигурация ML модели"""
    
    # Настройки обучения
    MODEL_TYPE: str = "RandomForest"
    MODEL_PATH: str = "models/quant_model.pkl"
    METADATA_PATH: str = "models/model_metadata.pkl"
    
    # Параметры модели
    RANDOM_FOREST_PARAMS: Dict[str, Any] = None
    MIN_TRAINING_RECORDS: int = 30
    TEST_SIZE: float = 0.2
    CROSS_VALIDATION_SPLITS: int = 5
    
    # Признаки для модели
    FEATURE_COLUMNS: List[str] = None
    
    # Пороги предсказаний
    MIN_PROBABILITY: float = 0.65
    CONFIDENCE_THRESHOLD: float = 0.7
    
    def __post_init__(self):
        if self.RANDOM_FOREST_PARAMS is None:
            self.RANDOM_FOREST_PARAMS = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'random_state': 42
            }
        
        if self.FEATURE_COLUMNS is None:
            self.FEATURE_COLUMNS = [
                'order_book_imbalance',
                'spread_percent',
                'cumulative_delta',
                'funding_rate',
                'buy_trades',
                'sell_trades',
                'total_trades',
                'volatility'
            ]

@dataclass
class TradingConfig:
    """Конфигурация торговли"""
    
    # Основные настройки
    ENABLED: bool = False  # 🔧 Безопасность по умолчанию
    MODE: str = "paper"  # paper, live
    INITIAL_BALANCE: float = 1000.0
    
    # Настройки позиции
    POSITION_SIZE: float = 0.1  # 10% от баланса
    MAX_POSITION_SIZE: float = 0.3  # 30% максимум
    LEVERAGE: int = 3
    
    # Риск-менеджмент
    STOP_LOSS_PERCENT: float = 2.0  # 2% стоп-лосс
    TAKE_PROFIT_PERCENT: float = 3.0  # 3% тейк-профит
    MAX_DRAWDOWN: float = 10.0  # 10% максимальная просадка
    
    # Торговые часы
    TRADING_HOURS_START: str = "00:00"
    TRADING_HOURS_END: str = "23:59"
    
    # Коэффициенты для разных режимов
    CONFIDENCE_MULTIPLIERS: Dict[str, float] = None
    
    def __post_init__(self):
        if self.CONFIDENCE_MULTIPLIERS is None:
            self.CONFIDENCE_MULTIPLIERS = {
                'high_confidence': 1.0,  # 80-100%
                'medium_confidence': 0.5,  # 60-80%
                'low_confidence': 0.2  # <60%
            }

@dataclass
class MonitoringConfig:
    """Конфигурация мониторинга"""
    
    # Интервалы проверок
    HEALTH_CHECK_INTERVAL: int = 60  # секунд
    PROGRESS_CHECK_INTERVAL: int = 120  # секунд
    DATA_QUALITY_CHECK_INTERVAL: int = 300  # секунд
    
    # Пороги для оповещений
    DATA_QUALITY_THRESHOLD: int = 50  # минимальный балл качества
    CONNECTION_QUALITY_THRESHOLD: str = "POOR"  # максимально допустимое качество
    MIN_ACTIVE_RECORDS: int = 10  # минимальное количество записей в минуту
    
    # Настройки отчетов
    ENABLE_DETAILED_REPORTS: bool = True
    SAVE_STATS_TO_FILE: bool = True
    STATS_FILE: str = "data/system_stats.json"

@dataclass
class LoggingConfig:
    """Конфигурация логирования"""
    
    # Уровни логирования
    CONSOLE_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    FILE_LEVEL: str = "DEBUG"
    
    # Файлы логов
    LOG_DIR: str = "logs"
    MAIN_LOG_FILE: str = "quantum_bot.log"
    ERROR_LOG_FILE: str = "errors.log"
    DATA_LOG_FILE: str = "data_log.csv"
    
    # Настройки формата
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # Ротация логов
    MAX_LOG_SIZE: int = 10 * 1024 * 1024  # 10 MB
    BACKUP_COUNT: int = 5
    
    def __post_init__(self):
        # Создаем директорию для логов
        os.makedirs(self.LOG_DIR, exist_ok=True)

@dataclass
class QuantumConfig:
    """Главная конфигурация Quantum Trading Bot"""
    
    # Версия и режим
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"  # development, testing, production
    
    # Основные настройки
    data: DataConfig = None
    strategy: StrategyConfig = None
    model: ModelConfig = None
    trading: TradingConfig = None
    monitoring: MonitoringConfig = None
    logging: LoggingConfig = None
    
    # Дополнительные настройки
    DEBUG_MODE: bool = True
    DRY_RUN: bool = True  # Режим тестирования без реальных сделок
    
    def __post_init__(self):
        # Инициализируем подконфиги если они не заданы
        if self.data is None:
            self.data = DataConfig()
        if self.strategy is None:
            self.strategy = StrategyConfig()
        if self.model is None:
            self.model = ModelConfig()
        if self.trading is None:
            self.trading = TradingConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
        if self.logging is None:
            self.logging = LoggingConfig()

# Глобальный экземпляр конфигурации
config = QuantumConfig()

# 🔧 Backward compatibility - старые константы для совместимости
SYMBOL = config.data.SYMBOL
TIMEFRAME = "1m"  # Оставляем для совместимости
WS_URL = config.data.WS_URL
CHANNELS = config.data.CHANNELS
FEATURE_WINDOW = config.data.FEATURE_WINDOW
MIN_PROBABILITY = config.model.MIN_PROBABILITY

def update_config_from_env():
    """Обновляет конфигурацию из переменных окружения"""
    import os
    
    # Данные
    if os.getenv('QUANTUM_SYMBOL'):
        config.data.SYMBOL = os.getenv('QUANTUM_SYMBOL')
    if os.getenv('QUANTUM_WS_URL'):
        config.data.WS_URL = os.getenv('QUANTUM_WS_URL')
    
    # Торговля
    if os.getenv('QUANTUM_TRADING_ENABLED'):
        config.trading.ENABLED = os.getenv('QUANTUM_TRADING_ENABLED').lower() == 'true'
    if os.getenv('QUANTUM_TRADING_MODE'):
        config.trading.MODE = os.getenv('QUANTUM_TRADING_MODE')
    
    # Логирование
    if os.getenv('QUANTUM_DEBUG'):
        config.DEBUG_MODE = os.getenv('QUANTUM_DEBUG').lower() == 'true'
    
    print("🔧 Конфигурация загружена из переменных окружения")

def save_config_to_file(filename: str = "config/quantum_config.json"):
    """Сохраняет конфигурацию в файл"""
    import json
    
    os.makedirs("config", exist_ok=True)
    
    config_dict = {
        'version': config.VERSION,
        'environment': config.ENVIRONMENT,
        'data': config.data.__dict__,
        'strategy': config.strategy.__dict__,
        'model': config.model.__dict__,
        'trading': config.trading.__dict__,
        'monitoring': config.monitoring.__dict__,
        'logging': config.logging.__dict__,
        'debug_mode': config.DEBUG_MODE,
        'dry_run': config.DRY_RUN
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Конфигурация сохранена: {filename}")

def load_config_from_file(filename: str = "config/quantum_config.json"):
    """Загружает конфигурацию из файла"""
    import json
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # Обновляем конфигурацию (упрощенная версия)
        if 'data' in config_dict:
            for key, value in config_dict['data'].items():
                if hasattr(config.data, key):
                    setattr(config.data, key, value)
        
        print(f"📁 Конфигурация загружена: {filename}")
        return True
        
    except FileNotFoundError:
        print(f"📁 Файл конфигурации не найден: {filename}")
        return False
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False

# 🔧 Автоматически загружаем конфигурацию при импорте
if load_config_from_file():
    print("✅ Конфигурация загружена из файла")
else:
    # Создаем дефолтную конфигурацию
    save_config_to_file()
    print("✅ Создана конфигурация по умолчанию")

# Обновляем из переменных окружения
update_config_from_env()
