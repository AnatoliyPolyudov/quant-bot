# В data_collector.py добавляем:
from baseline_strategy import baseline_strategy

# В методе update_features добавляем:
def update_features(self):
    """Обновляет фичи и управляет выводом/логированием"""
    current_time = time.time()
    
    # Всегда обновляем фичи
    features = feature_engine.get_all_features(
        self.order_book_data, 
        self.trade_data, 
        self.ticker_data
    )
    
    # Анализ бейзлайн-стратегией
    strategy_result = baseline_strategy.analyze_signal(features)
    
    # Логируем данные каждую минуту
    if current_time - self.last_data_log > 60:
        self.last_data_log = current_time
        data_logger.log_features(features)
    
    # Выводим в консоль каждые 30 секунд
    if current_time - self.last_feature_print > 30:
        self.last_feature_print = current_time
        
        print("\n" + "="*50)
        print("🎯 REAL-TIME FEATURES + BASELINE STRATEGY")
        print("="*50)
        
        print(f"📊 Order Book Imbalance: {features['order_book_imbalance']:.3f}")
        print(f"📏 Spread: {features['spread_percent']:.4f}%")
        print(f"📈 Cumulative Delta: {features['cumulative_delta']:.4f}")
        print(f"💰 Funding Rate: {features['funding_rate']:.6f}")
        print(f"🔄 Trades: {features['buy_trades']} buy / {features['sell_trades']} sell")
        
        print(f"\n🤖 BASELINE DECISION: {strategy_result['decision']}")
        print(f"🎯 Confidence: {strategy_result['confidence']:.1f}%")
        
        for signal in strategy_result['signals']:
            print(f"   {signal}")
            
        print(f"💾 Data points: {self.message_count}")
        print("="*50 + "\n")
