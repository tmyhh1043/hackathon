# attendance_app/utils/anomaly_detector.py

import pandas as pd
import os
import joblib
import requests

from dotenv import load_dotenv
import os

load_dotenv()



# モデル保存場所
MODEL_DIR = 'user_models'

def generate_text_with_api(prompt):
    api_key = os.getenv("API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json",
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return None

# 推論＋メッセージ生成
def predict_and_generate_message(user_id, attendance_row):
    # --- モデルパス（共通モデル） ---
    model_path = os.path.join(MODEL_DIR, "motivation_anomaly_model.pkl")
    
    if not os.path.exists(model_path):
        return "モデル未学習です。データ蓄積中📚"

    # --- モデルロード ---
    model = joblib.load(model_path)

    # --- 特徴量セット（7個揃える） ---
    X = pd.DataFrame([{
        'start_hour': attendance_row.get('start_hour', 0),
        'user_mean_working_minutes': attendance_row.get('user_mean_working_minutes', 480),
        'user_std_working_minutes': attendance_row.get('user_std_working_minutes', 30),
        'before_noon_flag': attendance_row.get('before_noon_flag', 1),
        'yesterday_overtime_flag': attendance_row.get('yesterday_overtime_flag', 0),
        'global_mean_working_minutes': attendance_row.get('global_mean_working_minutes', 470),
        'global_std_working_minutes': attendance_row.get('global_std_working_minutes', 40),
    }])

    X = X.fillna(0)  # 念のためNaN埋め

    # --- 推論 ---
    prediction = model.predict(X)[0]  # 0: 正常, 1: 来なさすぎ, 2: 頑張りすぎ

    # --- メッセージ生成 ---
    if prediction == 1:
        # 来なさすぎ
        prompt = "最近出勤が少なめなユーザーに、注意勧告をする日本語メッセージを短く作成してください。"
        message = generate_text_with_api(prompt)
        if message:
            return message
        else:
            return "最近お疲れ気味かな？無理せずゆっくりペースを取り戻そうね！"
        
    elif prediction == 2:
        # 頑張りすぎ
        prompt = "頑張りすぎているユーザーに、ねぎらいと休息を促す日本語メッセージを短く作成してください。"
        message = generate_text_with_api(prompt)
        if message:
            return message
        else:
            return "すごく頑張ってるね！体調も大事にしながら、無理しないでね✨"
        
    else:
        # 正常
        return "今日もお疲れ様でした！いつも安定した勤務、素晴らしいです😊"

