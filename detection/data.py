import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import xgboost as xgb
import matplotlib.pyplot as plt

# --- データ読み込み ---
df = pd.read_csv('./kintai-data.csv')
df['date'] = pd.to_datetime(df['date'])

# --- 特徴量作成 ---
feature_data = []

for date in sorted(df['date'].unique()):
    for user_id in df['user_id'].unique():
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
                yesterday_minutes = 480
        else:
            user_mean = 480
            user_std = 30
            yesterday_minutes = 480

        today_row = df[(df['user_id'] == user_id) & (df['date'] == date)]
        if today_row.empty:
            continue

        # start_hour取得
        start_hour_raw = today_row.iloc[0]['start_hour']

        if pd.isna(start_hour_raw):
            start_hour_float = 9.0
        elif isinstance(start_hour_raw, str):
            if ':' in start_hour_raw:
                hour, minute = map(int, start_hour_raw.split(':'))
                start_hour_float = hour + minute / 60
            else:
                start_hour_float = float(start_hour_raw)
        else:
            start_hour_float = float(start_hour_raw)

        # --- 直近1週間の全ユーザー勤務データからglobal_mean, global_stdを計算 ---
        one_week_ago = pd.to_datetime(date) - timedelta(days=7)
        global_past_week = df[(df['date'] < date) & (df['date'] >= one_week_ago)]

        if not global_past_week.empty:
            global_mean = global_past_week['working_minutes'].mean()
            global_std = global_past_week['working_minutes'].std()
        else:
            global_mean = 480
            global_std = 30

        # --- 特徴量セット ---
        z_score = (user_mean - global_mean) / global_std

        feature_row = {
            'user_id': user_id,
            'date': date,
            'start_hour': start_hour_float,
            'user_mean_working_minutes': user_mean,
            'user_std_working_minutes': user_std,
            'yesterday_overtime_flag': int(yesterday_minutes >= 540),
            'global_mean_working_minutes': global_mean,
            'global_std_working_minutes': global_std,
            'z_score': z_score
        }
        feature_data.append(feature_row)

# --- 特徴量DataFrame化 ---
feature_df = pd.DataFrame(feature_data)

# --- 保存 ---
feature_df.to_csv('../user_models/features_april.csv', index=False)
print("\n✅ 特徴量保存完了")
print(feature_df.head())

# --- パーセンタイル閾値を計算 ---
low_threshold = feature_df['z_score'].quantile(0.10)
high_threshold = feature_df['z_score'].quantile(0.90)

print(f"Low threshold (10%): {low_threshold:.3f}")
print(f"High threshold (90%): {high_threshold:.3f}")

# --- ターゲット列を作成 ---
feature_df['target'] = feature_df.apply(lambda row: 
    1 if row['z_score'] < low_threshold else
    2 if row['z_score'] > high_threshold or row['yesterday_overtime_flag'] == 1 else
    0, axis=1
)

# --- Zスコア分布ヒストグラム ---
plt.figure(figsize=(8,6))
plt.hist(feature_df['z_score'], bins=30, edgecolor='k')
plt.axvline(low_threshold, color='red', linestyle='--', label=f'{low_threshold:.2f} Threshold (10%)')
plt.axvline(high_threshold, color='green', linestyle='--', label=f'{high_threshold:.2f} Threshold (90%)')
plt.title('Distribution of Z-Score (User Mean vs Global)')
plt.xlabel('Z-Score')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True)
plt.savefig('./user_mean_vs_global_mean_distribution.png')
plt.show()
plt.close()

# --- 昨日オーバータイムフラグの棒グラフ ---
flag_counts = feature_df['yesterday_overtime_flag'].value_counts().sort_index()
plt.figure(figsize=(6,4))
plt.bar(flag_counts.index, flag_counts.values, tick_label=['Not Overtime', 'Overtime'])
plt.title('Yesterday Overtime (>= 540 minutes)')
plt.xlabel('Overtime Status')
plt.ylabel('Number of Users')
plt.grid(axis='y')
plt.savefig('./yesterday_overtime_flag_distribution.png')
plt.show()
plt.close()

# --- 特徴量カラム ---
feature_cols = [
    'start_hour',
    'user_mean_working_minutes',
    'user_std_working_minutes',
    'yesterday_overtime_flag',
    'global_mean_working_minutes',
    'global_std_working_minutes'
]

X = feature_df[feature_cols]
X = X.fillna(0)  # 念のためNaN埋める
y = feature_df['target']

# --- データ分割（8:2） ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- モデル学習 ---
model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.05,
    random_state=42,
    use_label_encoder=False,
    eval_metric='mlogloss'  # マルチクラス分類なのでこれ
)
model.fit(X_train, y_train)

# --- モデル評価 ---
y_pred = model.predict(X_test)

print("\n--- 分類レポート (正常/来なさすぎ/頑張りすぎ) ---")
print(classification_report(y_test, y_pred))

# --- モデル保存 ---
joblib.dump(model, '../user_models/motivation_anomaly_model.pkl')
print("\n✅ モデルを '../user_models/motivation_anomaly_model.pkl' に保存しました！")
