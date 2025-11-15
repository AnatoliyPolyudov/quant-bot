def log_features(self, features):
    """СОХРАНЯЕТ ВСЕ С TARGET НЕМЕДЛЕННО"""
    try:
        if features.get('target', 0) != 0:
            self.logged_count += 1
            with open(self.data_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    features['timestamp'],
                    features['order_book_imbalance'],
                    features['spread_percent'],
                    features['cumulative_delta'],
                    features['funding_rate'],
                    features['buy_trades'],
                    features['sell_trades'],
                    features['total_trades'],
                    features['current_price'],
                    features['target']
                ])
            print(f"💾 IMMEDIATE SAVE #{self.logged_count}: target={features['target']}")
    except Exception as e:
        print(f"❌ Data logging error: {e}")
