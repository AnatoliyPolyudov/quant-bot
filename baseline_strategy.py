# baseline_strategy.py
import numpy as np
from datetime import datetime

class BaselineStrategy:
    def __init__(self):
        # 🔧 ОПТИМИЗИРОВАННЫЕ ПАРАМЕТРЫ
        self.min_imbalance = 0.58      # 🔧 Оптимизировано
        self.min_delta = 2             # 🔧 Оптимизировано  
        self.max_spread = 0.025        # 🔧 Оптимизировано
        self.max_volatility = 0.8      # 🔧 Оптимизировано
        self.min_confidence = 60       # 🔧 НОВОЕ: минимальная уверенность
        
        # 🔧 НОВОЕ: Адаптивные параметры
        self.recent_signals = []
        self.market_regime = "NORMAL"  # NORMAL, VOLATILE, TRENDING
        self.last_regime_update = 0
        
        # 🔧 НОВОЕ: Веса для разных фич
        self.feature_weights = {
            'imbalance': 0.35,
            'delta': 0.25, 
            'spread': 0.15,
            'volatility': 0.15,
            'funding': 0.10
        }
        
    def update_market_regime(self, features):
        """Определяет текущий рыночный режим"""
        current_time = datetime.now().timestamp()
        
        # Обновляем режим не чаще чем раз в 30 секунд
        if current_time - self.last_regime_update < 30:
            return
            
        self.last_regime_update = current_time
        volatility = features.get('volatility', 0)
        imbalance = features.get('order_book_imbalance', 0.5)
        
        if volatility > 1.5:
            self.market_regime = "VOLATILE"
        elif abs(imbalance - 0.5) > 0.3:
            self.market_regime = "TRENDING" 
        else:
            self.market_regime = "NORMAL"
            
        # 🔧 Адаптируем параметры под режим
        if self.market_regime == "VOLATILE":
            self.min_imbalance = 0.62      # Более строгие условия
            self.min_delta = 3
            self.max_volatility = 0.6
        elif self.market_regime == "TRENDING":
            self.min_imbalance = 0.56      # Более чувствительные
            self.min_delta = 1
            self.max_volatility = 1.0
        else:
            self.min_imbalance = 0.58      # Нормальные условия
            self.min_delta = 2
            self.max_volatility = 0.8
    
    def calculate_composite_score(self, features):
        """Рассчитывает композитный скоринг на основе всех фич"""
        imbalance = features.get('order_book_imbalance', 0.5)
        delta = features.get('cumulative_delta', 0)
        spread = features.get('spread_percent', 0)
        volatility = features.get('volatility', 0)
        funding = features.get('funding_rate', 0)
        
        # 🔧 Нормализуем фичи для скоринга
        imbalance_score = max(0, (imbalance - 0.5) / 0.5)  # -1 to 1
        delta_score = np.tanh(delta / 10)  # Нормализуем дельту
        spread_score = max(0, 1 - (spread / self.max_spread))  # 0 to 1
        volatility_score = max(0, 1 - (volatility / self.max_volatility))  # 0 to 1
        funding_score = -np.tanh(funding * 1000)  # Отрицательный funding = хорошо
        
        # 🔧 Взвешенная сумма
        composite = (
            imbalance_score * self.feature_weights['imbalance'] +
            delta_score * self.feature_weights['delta'] +
            spread_score * self.feature_weights['spread'] +
            volatility_score * self.feature_weights['volatility'] +
            funding_score * self.feature_weights['funding']
        )
        
        return composite, {
            'imbalance_score': imbalance_score,
            'delta_score': delta_score, 
            'spread_score': spread_score,
            'volatility_score': volatility_score,
            'funding_score': funding_score
        }
    
    def analyze_momentum(self, features):
        """🔧 НОВОЕ: Анализ моментаum на основе нескольких сигналов"""
        imbalance = features.get('order_book_imbalance', 0.5)
        delta = features.get('cumulative_delta', 0)
        
        momentum_score = 0
        momentum_signals = []
        
        # Сильный imbalance
        if imbalance > 0.65:
            momentum_score += 2
            momentum_signals.append("💪 Сильный imbalance")
        elif imbalance > 0.6:
            momentum_score += 1
            momentum_signals.append("📊 imbalance в пользу buyers")
            
        # Сильная дельта
        if delta > 5:
            momentum_score += 2
            momentum_signals.append("🚀 Сильный inflow")
        elif delta > 2:
            momentum_score += 1
            momentum_signals.append("📈 Положительная дельта")
            
        # Комбинированный сигнал
        if imbalance > 0.6 and delta > 3:
            momentum_score += 1
            momentum_signals.append("🎯 Комбинированный сигнал")
            
        return momentum_score, momentum_signals
    
    def analyze_signal(self, features):
        """Улучшенный анализ сигналов с композитным скорингом"""
        # 🔧 НОВОЕ: Обновляем рыночный режим
        self.update_market_regime(features)
        
        imbalance = features.get('order_book_imbalance', 0.5)
        delta = features.get('cumulative_delta', 0)
        spread = features.get('spread_percent', 0)
        funding = features.get('funding_rate', 0)
        volatility = features.get('volatility', 0)
        
        signals = []
        warning_signals = []
        
        # 🔧 НОВОЕ: Композитный скоринг
        composite_score, score_details = self.calculate_composite_score(features)
        momentum_score, momentum_signals = self.analyze_momentum(features)
        
        # 🔧 УЛУЧШЕННЫЕ ПРАВИЛА С СИГНАЛАМИ РАЗНОЙ СИЛЫ
        
        # Правило 1: Imbalance с градацией
        if imbalance > 0.65:
            signals.append("💪 СИЛЬНЫЙ Imbalance {:.3f} > 0.65".format(imbalance))
        elif imbalance > self.min_imbalance:
            signals.append("📊 Imbalance {:.3f} > {}".format(imbalance, self.min_imbalance))
        elif imbalance < 0.35:
            signals.append("💪 СИЛЬНЫЙ Short Imbalance {:.3f} < 0.35".format(imbalance))
        elif imbalance < (1 - self.min_imbalance):
            signals.append("📊 Short Imbalance {:.3f} < {}".format(imbalance, 1 - self.min_imbalance))
        
        # Правило 2: Delta с градацией
        if delta > 5:
            signals.append("🚀 СИЛЬНЫЙ Delta {:.1f} > 5".format(delta))
        elif delta > self.min_delta:
            signals.append("📈 Delta {:.1f} > {}".format(delta, self.min_delta))
        elif delta < -5:
            signals.append("🚀 СИЛЬНЫЙ Short Delta {:.1f} < -5".format(delta))
        elif delta < -self.min_delta:
            signals.append("📈 Short Delta {:.1f} < -{}".format(delta, self.min_delta))
        
        # Правило 3: Spread
        if spread < self.max_spread:
            signals.append("📏 Spread {:.4f}% < {}%".format(spread, self.max_spread))
        else:
            warning_signals.append("❌ Spread {:.4f}% слишком высок".format(spread))
        
        # Правило 4: Волатильность
        if volatility < self.max_volatility:
            signals.append("📊 Volatility {:.3f}% < {}%".format(volatility, self.max_volatility))
        else:
            warning_signals.append("⚡ Volatility {:.3f}% слишком высока".format(volatility))
        
        # Правило 5: Funding
        if abs(funding) < 0.0001:
            signals.append("💰 Funding нейтральный")
        elif funding > 0.0005:
            warning_signals.append("🔴 Positive funding {:.6f} (SHORT bias)".format(funding))
        elif funding < -0.0005:
            signals.append("🟢 Negative funding {:.6f} (LONG bias)".format(funding))
        else:
            signals.append("💰 Funding {:.6f}".format(funding))
        
        # 🔧 НОВОЕ: Добавляем momentum сигналы
        signals.extend(momentum_signals)
        
        # 🔧 НОВОЕ: Информация о рыночном режиме
        signals.append("🎪 Режим: {}".format(self.market_regime))
        
        # 🔧 УЛУЧШЕННОЕ ПРИНЯТИЕ РЕШЕНИЙ
        base_buy_signal = (imbalance > self.min_imbalance and 
                          delta > self.min_delta and 
                          spread < self.max_spread and
                          volatility < self.max_volatility)
        
        base_sell_signal = (imbalance < (1 - self.min_imbalance) and 
                           delta < -self.min_delta and 
                           spread < self.max_spread and
                           volatility < self.max_volatility)
        
        # 🔧 НОВОЕ: Усиленные сигналы
        strong_buy_signal = (imbalance > 0.65 or delta > 5) and base_buy_signal
        strong_sell_signal = (imbalance < 0.35 or delta < -5) and base_sell_signal
        
        # 🔧 НОВОЕ: Композитное решение
        if composite_score > 0.1 and base_buy_signal:
            decision = "LONG"
            confidence = self.calculate_confidence(composite_score, momentum_score, features, warning_signals)
        elif composite_score < -0.1 and base_sell_signal:
            decision = "SHORT"
            confidence = self.calculate_confidence(-composite_score, momentum_score, features, warning_signals)
        else:
            decision = "HOLD"
            confidence = 0
        
        # 🔧 НОВОЕ: Усиливаем уверенность для сильных сигналов
        if strong_buy_signal and decision == "LONG":
            confidence = min(95, confidence + 15)
            signals.append("💪 УСИЛЕННЫЙ LONG сигнал")
        elif strong_sell_signal and decision == "SHORT":
            confidence = min(95, confidence + 15)
            signals.append("💪 УСИЛЕННЫЙ SHORT сигнал")
        
        # 🔧 НОВОЕ: Учитываем предупреждения
        if warning_signals:
            confidence = max(0, confidence - len(warning_signals) * 10)
            signals.extend(warning_signals)
        
        # 🔧 НОВОЕ: Минимальная уверенность
        if confidence < self.min_confidence and decision != "HOLD":
            decision = "HOLD"
            confidence = 0
            signals.append("🎯 Слишком низкая уверенность для сделки")
        
        return {
            'decision': decision,
            'confidence': confidence,
            'signals': signals,
            'composite_score': composite_score,
            'momentum_score': momentum_score,
            'imbalance': imbalance,
            'delta': delta,
            'spread': spread,
            'volatility': volatility,
            'market_regime': self.market_regime,
            'feature_scores': score_details
        }
    
    def calculate_confidence(self, composite_score, momentum_score, features, warning_signals):
        """🔧 НОВОЕ: Улучшенный расчет уверенности"""
        base_confidence = composite_score * 100
        
        # Бонус за momentum
        momentum_bonus = momentum_score * 8
        
        # Штраф за волатильность
        volatility = features.get('volatility', 0)
        vol_penalty = max(0, (volatility / self.max_volatility) * 20)
        
        # Штраф за предупреждения
        warning_penalty = len(warning_signals) * 12
        
        confidence = base_confidence + momentum_bonus - vol_penalty - warning_penalty
        
        # Ограничиваем диапазон
        confidence = max(0, min(95, confidence))
        
        return confidence

# Глобальный экземпляр
baseline_strategy = BaselineStrategy()
