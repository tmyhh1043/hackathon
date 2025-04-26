import sqlite3
import pandas as pd

# dbファイルへの接続
conn = sqlite3.connect('./db.sqlite3')
cursor = conn.cursor()

# attendance_attendancelogテーブルから全部データ取得
query = '''
SELECT attendance_attendancelog.id, auth_user.username, attendance_attendancelog.type, attendance_attendancelog.timestamp
FROM attendance_attendancelog
JOIN auth_user ON attendance_attendancelog.user_id = auth_user.id
ORDER BY attendance_attendancelog.timestamp ASC
'''

# pandasで直接読み込む
df = pd.read_sql_query(query, conn)

# 保存
df.to_csv('./detection/output_attendance.csv', index=False, encoding='utf-8-sig')

conn.close()

print("attendance_logをCSVに出力完了！✅")
