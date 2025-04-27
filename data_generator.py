import sqlite3
import pandas as pd
from datetime import datetime

# dbファイルへの接続
conn = sqlite3.connect('./db.sqlite3')
cursor = conn.cursor()

# user_idとusernameのマッピング辞書
user_mapping = {
    'user_1': 'hiro',
    'user_2': 'BBBB',
    'user_3': 'huji',
    'user_4': 'matsu',
    'user_5': 'yama'
}

# usernameから本物のUserテーブルのIDを取る
username_to_id = {}
for csv_user, real_username in user_mapping.items():
    cursor.execute("SELECT id FROM auth_user WHERE username = ?", (real_username,))
    result = cursor.fetchone()
    if result is None:
        print(f"{real_username} というユーザーが見つかりませんでした。")
        conn.close()
        exit()
    username_to_id[csv_user] = result[0]

# CSV読み込み
df = pd.read_csv('./detection/kintai-data.csv')

# CSVからAttendanceLogにINSERT
for _, row in df.iterrows():
    try:
        # CSVのuser_idから対応するDjangoユーザーIDを取得
        csv_user_id = row['user_id']
        if csv_user_id not in username_to_id:
            print(f"{csv_user_id} はマッピングに存在しません。スキップします。")
            continue

        real_user_id = username_to_id[csv_user_id]

        # 出勤（in）データ
        start_timestamp = datetime.strptime(f"{row['date']} {row['start_hour']}", "%Y/%m/%d %H:%M")
        cursor.execute('''
            INSERT INTO attendance_attendancelog (user_id, type, timestamp)
            VALUES (?, ?, ?)
        ''', (real_user_id, 'in', start_timestamp))

        # 退勤（out）データ
        finish_timestamp = datetime.strptime(f"{row['date']} {row['finish_hour']}", "%Y/%m/%d %H:%M")
        cursor.execute('''
            INSERT INTO attendance_attendancelog (user_id, type, timestamp)
            VALUES (?, ?, ?)
        ''', (real_user_id, 'out', finish_timestamp))

    except Exception as e:
        print(f"エラー発生: {e}（行データ: {row})")

# 保存して閉じる
conn.commit()
conn.close()

print("すべてのデータを正しいユーザーにマッピングして挿入完了！✅")
