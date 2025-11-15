# baseline_strategy.py
class BaselineStrategy:
    def __init__(self):
        self.min_imbalance = 0.6
        self.min_delta = 5  # Уменьшено
        self.max_spread = 0.03  # Увеличено до 0.03%
        
    def analyze_signal(self, features):
        imbalance = features.get('order_book_imbalance', 0.5)
        delta = features.get('cumulative_delta', 0)
        spread = features.get('spread_percent', 0)
        funding = features.get('funding_rate', 0)
        
        signals = []
        
        if imbalance > self.min_imbalance:
            signals.append(f"📊 Imbalance {imbalance:.3f} > {self.min_imbalance}")
        
        if delta > self.min_delta:
            signals.append(f"📈 Delta {delta:.1f} > {self.min_delta}")
        
        if spread < self.max_spread:
            signals.append(f"📏 Spread {spread:.4f}% < {self.max_spread}%")
        else:
            signals.append(f"❌ Spread {spread:.4f}% слишком высок")
        
        if abs(funding) < 0.0001:
            signals.append("💰 Funding нейтральный")
        else:
            signals.append(f"⚠️ Funding {funding:.6f}")
        
        buy_signal = (imbalance > self.min_imbalance and 
                     delta > self.min_delta and 
                     spread < self.max_spread)
        
        sell_signal = (imbalance < (1 - self.min_imbalance) and 
                      delta < -self.min_delta and 
                      spread < self.max_spread)
        
        if buy_signal:
            decision = "LONG"
            confidence = min(imbalance * 100, 95)
        elif sell_signal:
            decision = "SHORT" 
            confidence = min((1 - imbalance) * 100, 95)
        else:
            decision = "HOLD"
            confidence = 0
        
        return {
            'decision': decision,
            'confidence': confidence,
            'signals': signals,
            'imbalance': imbalance,
            'delta': delta,
            'spread': spread
        }

baseline_strategy = BaselineStrategy()
