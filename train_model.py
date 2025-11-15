# train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.utils import class_weight
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns

def load_training_data():
    """Загружает данные для обучения с улучшенной проверкой"""
    data_file = "data/training_data.csv"
    
    if not os.path.exists(data_file):
        print("❌ Файл с данными не найден. Сначала соберите данные.")
        return None
    
    try:
        df = pd.read_csv(data_file)
        print(f"📊 Загружено {len(df)} записей")
        
        # Проверяем наличие колонки target
        if 'target' not in df.columns:
            print("❌ Колонка 'target' не найдена в данных")
            return None
            
        # Проверяем, есть ли размеченные данные
        target_data = df['target'].dropna()
        if len(target_data) == 0:
            print("❌ Нет размеченных данных (target). Продолжайте сбор данных.")
            return None
        
        print(f"🎯 Размеченных записей: {len(target_data)}")
        
        return df
        
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return None

def detailed_data_analysis(df):
    """Детальный анализ данных"""
    print("\n🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ДАННЫХ:")
    
    # Убираем строки без target
    df_labeled = df.dropna(subset=['target'])
    df_labeled['target'] = df_labeled['target'].astype(int)
    
    # Распределение target
    target_counts = df_labeled['target'].value_counts().sort_index()
    total_labeled = len(df_labeled)
    
    print(f"📊 Распределение target ({total_labeled} записей):")
    for target_val in [-1, 0, 1]:
        count = target_counts.get(target_val, 0)
        percentage = count / total_labeled * 100
        symbol = "🔴" if target_val == -1 else "⚪" if target_val == 0 else "🟢"
        print(f"   {symbol} Target {target_val}: {count} записей ({percentage:.1f}%)")
    
    # Анализ признаков
    print(f"\n📈 Статистика признаков:")
    feature_columns = ['order_book_imbalance', 'spread_percent', 'cumulative_delta', 
                      'funding_rate', 'volatility']
    
    for feature in feature_columns:
        if feature in df_labeled.columns:
            stats = df_labeled[feature].describe()
            print(f"   {feature}:")
            print(f"      min={stats['min']:.6f}, max={stats['max']:.6f}")
            print(f"      mean={stats['mean']:.6f}, std={stats['std']:.6f}")
            print(f"      non-zero: {(df_labeled[feature] != 0).sum()}/{len(df_labeled)}")
    
    # Проверка на постоянные значения
    constant_features = []
    for feature in feature_columns:
        if feature in df_labeled.columns and df_labeled[feature].nunique() <= 1:
            constant_features.append(feature)
    
    if constant_features:
        print(f"⚠️  Постоянные признаки: {constant_features}")
    
    # Проверка корреляции с target
    print(f"\n📊 Корреляция признаков с target:")
    for feature in feature_columns:
        if feature in df_labeled.columns:
            correlation = df_labeled[feature].corr(df_labeled['target'])
            print(f"   {feature}: {correlation:.3f}")
    
    return df_labeled

def create_baseline_model(df):
    """Создает бейзлайн модель на основе простых правил"""
    print("\n🤖 БЕЙЗЛАЙН МОДЕЛЬ (правила):")
    
    # Правило 1: Imbalance
    df['baseline_imbalance'] = (df['order_book_imbalance'] > 0.6).astype(int)
    accuracy_imbalance = accuracy_score(df['target'] == 1, df['baseline_imbalance'])
    print(f"📊 Imbalance > 0.6 accuracy: {accuracy_imbalance:.3f}")
    
    # Правило 2: Delta
    df['baseline_delta'] = (df['cumulative_delta'] > 0).astype(int)
    accuracy_delta = accuracy_score(df['target'] == 1, df['baseline_delta'])
    print(f"📈 Delta > 0 accuracy: {accuracy_delta:.3f}")
    
    # Правило 3: Combined
    df['baseline_combined'] = ((df['order_book_imbalance'] > 0.6) & 
                              (df['cumulative_delta'] > 0)).astype(int)
    accuracy_combined = accuracy_score(df['target'] == 1, df['baseline_combined'])
    print(f"🎯 Combined rule accuracy: {accuracy_combined:.3f}")
    
    # Бейзлайн для всех классов
    baseline_majority = (df['target'] == 0).mean()
    print(f"📊 Majority class (HOLD) accuracy: {baseline_majority:.3f}")

def handle_class_imbalance(df):
    """Обрабатывает дисбаланс классов"""
    print("\n⚖️  ОБРАБОТКА ДИСБАЛАНСА КЛАССОВ:")
    
    target_counts = df['target'].value_counts()
    print(f"Исходное распределение: {target_counts.to_dict()}")
    
    # Вычисляем веса классов
    class_weights = class_weight.compute_class_weight(
        class_weight='balanced',
        classes=np.array([-1, 0, 1]),
        y=df['target']
    )
    
    weight_dict = {-1: class_weights[0], 0: class_weights[1], 1: class_weights[2]}
    print(f"Веса классов: {weight_dict}")
    
    return weight_dict

def train_ml_model(df):
    """Обучает ML модель с улучшенной обработкой"""
    print("\n🧠 ОБУЧЕНИЕ ML МОДЕЛИ...")
    
    # Признаки для модели
    feature_columns = [
        'order_book_imbalance',
        'spread_percent', 
        'cumulative_delta',
        'funding_rate',
        'buy_trades',
        'sell_trades', 
        'total_trades',
        'volatility'
    ]
    
    # Проверяем наличие всех признаков
    missing_features = [f for f in feature_columns if f not in df.columns]
    if missing_features:
        print(f"⚠️  Отсутствуют признаки: {missing_features}")
        # Используем только доступные признаки
        feature_columns = [f for f in feature_columns if f in df.columns]
    
    X = df[feature_columns]
    y = df['target']
    
    # Убираем NaN
    mask = ~X.isna().any(axis=1)
    X = X[mask]
    y = y[mask]
    
    print(f"📊 Данные для обучения: {len(X)} записей")
    print(f"🎯 Признаки: {feature_columns}")
    
    if len(X) < 50:
        print(f"❌ Недостаточно данных для обучения. Нужно минимум 50, сейчас: {len(X)}")
        return None
    
    # Обрабатываем дисбаланс классов
    class_weights = handle_class_imbalance(pd.DataFrame({'target': y}))
    
    # Кросс-валидация с временными рядами
    tscv = TimeSeriesSplit(n_splits=min(5, len(X) // 10))
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight=class_weights,
        max_depth=10,
        min_samples_split=5
    )
    
    # Кросс-валидация
    print("📊 Запуск кросс-валидации...")
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
    
    # Детальная оценка модели
    y_pred = model.predict(X)
    print(f"\n📈 Точность на обучающих данных: {accuracy_score(y, y_pred):.3f}")
    
    # Матрица ошибок
    cm = confusion_matrix(y, y_pred)
    print(f"📊 Матрица ошибок:")
    print(f"   True -1: {cm[0]}")
    print(f"   True  0: {cm[1]}") 
    print(f"   True  1: {cm[2]}")
    
    return model, feature_columns

def save_model(model, feature_columns, filename="models/quant_model.pkl"):
    """Сохраняет обученную модель и метаданные"""
    os.makedirs("models", exist_ok=True)
    
    # Сохраняем модель
    joblib.dump(model, filename)
    
    # Сохраняем метаданные
    metadata = {
        'feature_columns': feature_columns,
        'model_type': 'RandomForest',
        'timestamp': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        'classes': model.classes_.tolist() if hasattr(model, 'classes_') else []
    }
    joblib.dump(metadata, "models/model_metadata.pkl")
    
    print(f"💾 Модель сохранена: {filename}")
    print(f"📝 Метаданные сохранены: models/model_metadata.pkl")
    print(f"🎯 Классы модели: {metadata['classes']}")

def plot_feature_importance(model, feature_columns):
    """Визуализирует важность признаков"""
    try:
        importance_df = pd.DataFrame({
            'feature': feature_columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=True)
        
        plt.figure(figsize=(10, 6))
        plt.barh(importance_df['feature'], importance_df['importance'])
        plt.xlabel('Важность признака')
        plt.title('Важность признаков в модели')
        plt.tight_layout()
        plt.savefig('models/feature_importance.png', dpi=300, bbox_inches='tight')
        print("📊 График важности признаков сохранен: models/feature_importance.png")
        plt.close()
    except Exception as e:
        print(f"⚠️  Не удалось создать график: {e}")

def main():
    print("🚀 ЗАПУСК ОБУЧЕНИЯ МОДЕЛИ...")
    
    # Загружаем данные
    df = load_training_data()
    if df is None:
        return
    
    # Детальный анализ данных
    df_labeled = detailed_data_analysis(df)
    if df_labeled is None or len(df_labeled) == 0:
        print("❌ Нет данных для обучения")
        return
    
    # Бейзлайн модель
    create_baseline_model(df_labeled)
    
    # ML модель (если достаточно данных)
    if len(df_labeled) >= 30:
        print(f"\n🔧 Обучение на {len(df_labeled)} записях...")
        result = train_ml_model(df_labeled)
        if result:
            model, feature_columns = result
            save_model(model, feature_columns)
            plot_feature_importance(model, feature_columns)
            print("\n🎉 Обучение завершено! Модель готова к использованию.")
        else:
            print("❌ Ошибка обучения модели")
    else:
        print(f"📊 Продолжайте сбор данных. Сейчас: {len(df_labeled)}/30")

if __name__ == "__main__":
    main()
