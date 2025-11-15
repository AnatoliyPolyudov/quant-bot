# baseline_strategy.py
class BaselineStrategy:
    def __init__(self):
        self.min_imbalance = 0.55  # 🔧 Уменьшено для большей чувствительности
        self.min_delta = 3         # 🔧 Уменьшено
        self.max_spread = 0.03
        self.max_volatility = 0.5  # 🔧 ДОБАВЛЕНО: максимальная волатильность
        
    def analyze_signal(self, features):
        """Анализирует фичи с учетом волатильности"""
        imbalance = features.get('order_book_imbalance', 0.5)
        delta = features.get('cumulative_delta', 0)
        spread = features.get('spread_percent', 0)
        funding = features.get('funding_rate', 0)
        volatility = features.get('volatility', 0)  # 🔧 НОВАЯ ФИЧА
        
        signals = []
        
        # Правило 1: Imbalance
        if imbalance > self.min_imbalance:
            signals.append(f"📊 Imbalance {imbalance:.3f} > {self.min_imbalance}")
        
        # Правило 2: Delta
        if delta > self.min_delta:
            signals.append(f"📈 Delta {delta:.1f} > {self.min_delta}")
        
        # Правило 3: Spread
        if spread < self.max_spread:
            signals.append(f"📏 Spread {spread:.4f}% < {self.max_spread}%")
        else:
            signals.append(f"❌ Spread {spread:.4f}% слишком высок")
        
        # 🔧 ПРАВИЛО 4: Волатильность
        if volatility < self.max_volatility:
            signals.append(f"📊 Volatility {volatility:.3f}% < {self.max_volatility}%")
        else:
            signals.append(f"⚡ Volatility {volatility:.3f}% слишком высока")
        
        # Правило 5: Funding
        if abs(funding) < 0.0001:
            signals.append("💰 Funding нейтральный")
        else:
            signals.append(f"⚠️ Funding {funding:.6f}")
        
        # 🔧 УЛУЧШЕННОЕ принятие решения
        buy_signal = (imbalance > self.min_imbalance and 
                     delta > self.min_delta and 
                     spread < self.max_spread and
                     volatility < self.max_volatility)  # 🔧 Учет волатильности
        
        sell_signal = (imbalance < (1 - self.min_imbalance) and 
                      delta < -self.min_delta and 
                      spread < self.max_spread and
                      volatility < self.max_volatility)  # 🔧 Учет волатильности
        
        if buy_signal:
            decision = "LONG"
            # 🔧 Адаптивная уверенность на основе волатильности
            base_confidence = min(imbalance * 100, 95)
            vol_penalty = max(0, (volatility / self.max_volatility) * 20)
            confidence = max(0, base_confidence - vol_penalty)
        elif sell_signal:
            decision = "SHORT" 
            base_confidence = min((1 - imbalance) * 100, 95)
            vol_penalty = max(0, (volatility / self.max_volatility) * 20)
            confidence = max(0, base_confidence - vol_penalty)
        else:
            decision = "HOLD"
            confidence = 0
        
        return {
            'decision': decision,
            'confidence': confidence,
            'signals': signals,
            'imbalance': imbalance,
            'delta': delta,
            'spread': spread,
            'volatility': volatility  # 🔧 Добавлено в вывод
        }

# Глобальный экземпляр
baseline_strategy = BaselineStrategy()
