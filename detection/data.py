import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


# --- パラメータ設定 ---
n_users = 10  # ユーザ数
start_date = datetime(2025, 4, 1)
end_date = datetime(2025, 4, 26)

# 平日のみ（日付リスト）
dates = pd.date_range(start=start_date, end=end_date, freq='B')
users = [f"user_{i}" for i in range(1, n_users + 1)]

data = []

# --- ダミーデータ作成 ---
for user_id in users:
    base_start_hour = random.uniform(8.0, 9.0)
    base_work_minutes = random.randint(450, 510)  # 7.5〜8.5時間勤務

    for date in dates:
        start_hour = base_start_hour + np.random.normal(0, 0.3)
        working_minutes = base_work_minutes + np.random.normal(0, 30)

        # 来なさすぎパターン
        if random.random() < 0.25:
            start_hour += random.uniform(1.5, 3.0)
            working_minutes -= random.uniform(100, 200)

        # 働きすぎパターン
        if random.random() < 0.25:
            working_minutes += random.uniform(120, 180)

        data.append({
            'user_id': user_id,
            'date': date.date(),
            'start_hour': round(start_hour, 2),
            'working_minutes': max(0, int(working_minutes))
        })

# --- DataFrame化 ---
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(by=['date', 'user_id']).reset_index(drop=True)

# 保存
os.makedirs('../user_models', exist_ok=True)
df.to_csv('../user_models/dummy_attendance_april.csv', index=False)
print("\n✅ ダミーデータ保存完了")

# --- 特徴量作成 ---
feature_data = []

for date in sorted(df['date'].unique()):
    global_past = df[df['date'] < date]
    global_mean = global_past['working_minutes'].mean() if not global_past.empty else 480
    global_std = global_past['working_minutes'].std() if not global_past.empty else 30

    for user_id in users:
        user_past = df[(df['user_id'] == user_id) & (df['date'] < date)].sort_values(by='date')

        if not user_past.empty:
            one_week_ago = pd.to_datetime(date) - timedelta(days=7)
            user_past_week = user_past[user_past['date'] >= one_week_ago]

            user_mean = user_past_week['working_minutes'].mean()
            user_std = user_past_week['working_minutes'].std()

            yesterday = pd.to_datetime(date) - timedelta(days=1)
            yesterday_data = user_past[user_past['date'] == yesterday]

            if not yesterday_data.empty:
                yesterday_minutes = yesterday_data.iloc[0]['working_minutes']
            else:
                yesterday_minutes = 480  # デフォルト
        else:
            user_mean = 480
            user_std = 30
            yesterday_minutes = 480

        today_row = df[(df['user_id'] == user_id) & (df['date'] == date)]
        if today_row.empty:
            continue

        start_hour = today_row.iloc[0]['start_hour']

        # 特徴量作成
        feature_row = {
            'user_id': user_id,
            'date': date,
            'start_hour': start_hour,
            'user_mean_working_minutes': user_mean,
            'user_std_working_minutes': user_std,
            'before_noon_flag': int(start_hour < 12.0),
            'yesterday_overtime_flag': int(yesterday_minutes >= 300),  # 昨日5時間以上勤務
            'global_mean_working_minutes': global_mean,
            'global_std_working_minutes': global_std,
        }

        # ターゲット設定
        if start_hour >= 11.0:
            target = 1  # 出勤遅すぎ（来なさすぎ）
        elif user_mean < global_mean * 0.85:
            target = 1  # 個人がチームより極端に少ない（来なさすぎ）
        elif user_mean > global_mean * 1.15:
            target = 2  # 頑張りすぎ
        else:
            target = 0  # 正常

        feature_row['target'] = target

        feature_data.append(feature_row)

# --- 特徴量DataFrame化 ---
feature_df = pd.DataFrame(feature_data)

# 保存
feature_df.to_csv('../user_models/features_april.csv', index=False)
print("\n✅ 特徴量保存完了")
print(feature_df.head())

# 特徴量カラム
feature_cols = [
    'start_hour',
    'user_mean_working_minutes',
    'user_std_working_minutes',
    'before_noon_flag',
    'yesterday_overtime_flag',
    'global_mean_working_minutes',
    'global_std_working_minutes'
]

X = feature_df[feature_cols]
X = X.fillna(X.mean())  # 念のためNaN埋める
y = feature_df['target']

# --- データ分割（8:2） ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- モデル学習 ---
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    random_state=42,
    class_weight='balanced'  # クラス不均衡対応
)
model.fit(X_train, y_train)

# --- モデル評価 ---
y_pred = model.predict(X_test)

print("\n--- 分類レポート (正常/来なさすぎ/頑張りすぎ) ---")
print(classification_report(y_test, y_pred))

# --- モデル保存 ---
joblib.dump(model, '../user_models/motivation_anomaly_model.pkl')
print("\n✅ モデルを '../user_models/motivation_anomaly_model.pkl' に保存しました！")