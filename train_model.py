# train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def load_training_data():
    """Загружает данные для обучения"""
    data_file = "data/training_data.csv"
    
    if not os.path.exists(data_file):
        print("❌ Файл с данными не найден. Сначала соберите данные.")
        return None
    
    df = pd.read_csv(data_file)
    print(f"📊 Загружено {len(df)} записей")
    
    # Проверяем, есть ли target
    if 'target' not in df.columns or df['target'].isna().all():
        print("❌ Нет размеченных данных (target). Продолжайте сбор данных.")
        return None
    
    # Убираем строки без target
    df = df.dropna(subset=['target'])
    df['target'] = df['target'].astype(int)
    
    print(f"🎯 Размеченных записей: {len(df)}")
    print(f"📈 Распределение target: {df['target'].value_counts().to_dict()}")
    
    return df

def create_baseline_model(df):
    """Создает бейзлайн модель на основе простых правил"""
    print("\n🤖 БЕЙЗЛАЙН МОДЕЛЬ (правила):")
    
    # Правило 1: Imbalance > 0.6 = покупать
    df['baseline_imbalance'] = (df['order_book_imbalance'] > 0.6).astype(int)
    accuracy_imbalance = accuracy_score(df['target'] == 1, df['baseline_imbalance'])
    print(f"📊 Imbalance > 0.6 accuracy: {accuracy_imbalance:.3f}")
    
    # Правило 2: Delta > 0 = покупать
    df['baseline_delta'] = (df['cumulative_delta'] > 0).astype(int)
    accuracy_delta = accuracy_score(df['target'] == 1, df['baseline_delta'])
    print(f"📈 Delta > 0 accuracy: {accuracy_delta:.3f}")
    
    # Комбинированное правило
    df['baseline_combined'] = ((df['order_book_imbalance'] > 0.6) & 
                              (df['cumulative_delta'] > 0)).astype(int)
    accuracy_combined = accuracy_score(df['target'] == 1, df['baseline_combined'])
    print(f"🎯 Combined rule accuracy: {accuracy_combined:.3f}")

def train_ml_model(df):
    """Обучает ML модель"""
    print("\n🧠 ОБУЧЕНИЕ ML МОДЕЛИ...")
    
    # Признаки для модели
    feature_columns = [
        'order_book_imbalance',
        'spread_percent', 
        'cumulative_delta',
        'funding_rate',
        'buy_trades',
        'sell_trades',
        'total_trades'
    ]
    
    # Проверяем наличие всех признаков
    missing_features = [f for f in feature_columns if f not in df.columns]
    if missing_features:
        print(f"❌ Отсутствуют признаки: {missing_features}")
        return None
    
    X = df[feature_columns]
    y = df['target']
    
    # Убираем NaN
    mask = ~X.isna().any(axis=1)
    X = X[mask]
    y = y[mask]
    
    print(f"📊 Данные для обучения: {len(X)} записей")
    
    # Кросс-валидация с временными рядами
    tscv = TimeSeriesSplit(n_splits=5)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # Кросс-валидация
    scores = cross_val_score(model, X, y, cv=tscv, scoring='accuracy')
    print(f"📊 Кросс-валидация accuracy: {scores.mean():.3f} (+/- {scores.std() * 2:.3f})")
    
    # Обучение финальной модели
    model.fit(X, y)
    print("✅ Модель обучена!")
    
    # Важность признаков
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🎯 ВАЖНОСТЬ ПРИЗНАКОВ:")
    for _, row in feature_importance.iterrows():
        print(f"  {row['feature']}: {row['importance']:.3f}")
    
    return model

def save_model(model, filename="models/quant_model.pkl"):
    """Сохраняет обученную модель"""
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, filename)
    print(f"💾 Модель сохранена: {filename}")

def main():
    print("🚀 ЗАПУСК ОБУЧЕНИЯ МОДЕЛИ...")
    
    # Загружаем данные
    df = load_training_data()
    if df is None or len(df) < 50:
        print(f"❌ Недостаточно данных для обучения. Нужно минимум 50 записей, сейчас: {len(df) if df is not None else 0}")
        return
    
    # Бейзлайн модель
    create_baseline_model(df)
    
    # ML модель (если достаточно данных)
    if len(df) >= 50:
        model = train_ml_model(df)
        if model:
            save_model(model)
            print("\n🎉 Обучение завершено! Модель готова к использованию.")
    else:
        print(f"📊 Продолжайте сбор данных. Сейчас: {len(df)}/50")

if __name__ == "__main__":
    main()
