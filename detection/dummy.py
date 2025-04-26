import pandas as pd
import joblib

# 複数パターンのダミーデータ作成
dummy_data = pd.DataFrame([
    # 正常パターン
    {
        'start_hour': 9.0,  
        'user_mean_working_minutes': 480,
        'user_std_working_minutes': 20,
        'yesterday_overtime_flag': 0,
        'global_mean_working_minutes': 480,
        'global_std_working_minutes': 30
    },
    # 来なさすぎ（出勤時間が遅い）
    {
        'start_hour': 13.0,  
        'user_mean_working_minutes': 480,
        'user_std_working_minutes': 20,
        'yesterday_overtime_flag': 0,
        'global_mean_working_minutes': 480,
        'global_std_working_minutes': 30
    },
    # 来なさすぎ（勤務時間がかなり少ない）
    {
        'start_hour': 9.0,  
        'user_mean_working_minutes': 300,  # かなり短い
        'user_std_working_minutes': 15,
        'yesterday_overtime_flag': 0,
        'global_mean_working_minutes': 480,
        'global_std_working_minutes': 30
    },
    # 頑張りすぎ（勤務時間がかなり長い）
    {
        'start_hour': 9.0,  
        'user_mean_working_minutes': 800,  # かなり長い
        'user_std_working_minutes': 40,
        'yesterday_overtime_flag': 1,
        'global_mean_working_minutes': 480,
        'global_std_working_minutes': 30
    },
    # 昨日もオーバーワーク
    {
        'start_hour': 10.0,
        'user_mean_working_minutes': 500,
        'user_std_working_minutes': 35,
        'yesterday_overtime_flag': 1,
        'global_mean_working_minutes': 480,
        'global_std_working_minutes': 30
    },
])

print(dummy_data)
# モデルをロード
model = joblib.load('../user_models/motivation_anomaly_model.pkl')

# 推論
predictions = model.predict(dummy_data)

# 結果表示
for i, pred in enumerate(predictions):
    label = {0: "正常", 1: "来なさすぎ", 2: "頑張りすぎ"}.get(pred, "未知")
    print(f"サンプル{i+1}: 予測クラス = {pred} ({label})")
