# attendance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog
from django.contrib.auth import logout
from django.core.paginator import Paginator
from .weather import get_osaka_weather
from django.utils import timezone
from django.contrib import messages
from datetime import date, datetime, timedelta
from collections import defaultdict
from datetime import timedelta
from .utils.anomaly_detector import predict_and_generate_message 
import pandas as pd
from django.contrib.auth.models import User


def top_view(request):
    # 大阪の天気情報を取得
    weather_info = get_osaka_weather()
    # 今日の日付を取得
    today = date.today()
    
    # 出勤中のユーザー情報を取得
    working_users = AttendanceLog.objects.filter(
        type='in',  # 出勤ログのみ
        timestamp__date=today  # 今日のデータのみ
    ).exclude(  # 退勤済みのユーザを除外
        user__in=AttendanceLog.objects.filter(
            type='out',
            timestamp__date=today
        ).values('user')
    )
    
    # 天気情報と出勤中のユーザー情報をテンプレートに渡す
    return render(request, 'attendance/top.html', {'weather_info': weather_info, 'working_users': working_users})

@login_required
def record_and_redirect(request, direction):
    today = timezone.now().date()
    if direction == "in":
        # すでに今日出勤済みならスキップ
        already_clocked_in = AttendanceLog.objects.filter(
            user=request.user,
            type='in',
            timestamp__date=today
        ).exists()
        
        if already_clocked_in:
            return redirect('record_attend')
        
        now = timezone.now()
        AttendanceLog.objects.create(
            user=request.user,
            type='in',
            timestamp=now
        )
        
        # --- 出勤時間（start_hour） ---
        start_hour = now.hour + now.minute / 60

        # --- 昨日の在籍時間（working_minutes） ---
        yesterday = today - timedelta(days=1)

        yesterday_in = AttendanceLog.objects.filter(
            user=request.user,
            type='in',
            timestamp__date=yesterday
        ).order_by('timestamp').first()

        yesterday_out = AttendanceLog.objects.filter(
            user=request.user,
            type='out',
            timestamp__date=yesterday
        ).order_by('timestamp').first()

        if yesterday_in and yesterday_out:
            working_minutes = int((yesterday_out.timestamp - yesterday_in.timestamp).total_seconds() // 60)
        else:
            working_minutes = 480  # デフォルト8時間勤務

        # --- 直近1週間の個人勤務データ ---
        one_week_ago = today - timedelta(days=7)
        user_past_out_logs = AttendanceLog.objects.filter(
            user=request.user,
            type='out',
            timestamp__date__range=[one_week_ago, yesterday]
        )

        user_durations = []
        for out_log in user_past_out_logs:
            in_log = AttendanceLog.objects.filter(
                user=request.user,
                type='in',
                timestamp__lt=out_log.timestamp
            ).order_by('-timestamp').first()
            if in_log:
                duration = (out_log.timestamp - in_log.timestamp).total_seconds() / 60
                user_durations.append(duration)

        if user_durations:
            user_mean_working_minutes = sum(user_durations) / len(user_durations)
            user_std_working_minutes = pd.Series(user_durations).std()
        else:
            user_mean_working_minutes = 480
            user_std_working_minutes = 30

        # --- 全体勤務データ ---
        global_out_logs = AttendanceLog.objects.filter(
            type='out',
            timestamp__date__lt=today
        )

        global_durations = []
        for out_log in global_out_logs:
            in_log = AttendanceLog.objects.filter(
                user=out_log.user,
                type='in',
                timestamp__lt=out_log.timestamp
            ).order_by('-timestamp').first()
            if in_log:
                duration = (out_log.timestamp - in_log.timestamp).total_seconds() / 60
                global_durations.append(duration)

        if global_durations:
            global_mean_working_minutes = sum(global_durations) / len(global_durations)
            global_std_working_minutes = pd.Series(global_durations).std()
        else:
            global_mean_working_minutes = 470
            global_std_working_minutes = 40

        # --- attendance_rowを7個の特徴量で作成 ---
        attendance_row = {
            'start_hour': start_hour,
            'user_mean_working_minutes': user_mean_working_minutes,
            'user_std_working_minutes': user_std_working_minutes,
            'before_noon_flag': int(start_hour < 12.0),
            'yesterday_overtime_flag': int(working_minutes >= 540),
            'global_mean_working_minutes': global_mean_working_minutes,
            'global_std_working_minutes': global_std_working_minutes
        }

        # --- モチベ管理メッセージ推論 ---
        message = predict_and_generate_message(request.user.id, attendance_row)

        # --- メッセージをセッション保存 ---
        request.session['attendance_message'] = message
    
    elif direction == "out":
        already_clocked_out = AttendanceLog.objects.filter(
            user=request.user,
            type='out',
            timestamp__date=today
        ).exists()
        
        if already_clocked_out:
            return redirect('record_leave') 
        
        # まだ出勤していない場合
        already_clocked_in = AttendanceLog.objects.filter(
            user=request.user,
            type='in',
            timestamp__date=today
        ).exists()
        if not already_clocked_in:
            return redirect('not_record')

        # 出勤ログを保存
        AttendanceLog.objects.create(
            user=request.user,
            type='out',
            timestamp=timezone.now()
        )
        
    return redirect('record_done')

@login_required
def record_done(request):
    message = request.session.pop('attendance_message', None)
    logout(request)
    return render(request, 'attendance/record_done.html', {'message': message})

@login_required
def record_attend(request):
    logout(request)
    return render(request, 'attendance/record_attend.html')

@login_required
def record_leave(request):
    logout(request)
    return render(request, 'attendance/record_leave.html')

@login_required
def not_record(request):
    logout(request)
    return render(request, 'attendance/not_record.html')


@login_required
def history_view(request):
    week_number = int(request.GET.get('week', 0))  # 週番号（0: 今週、1: 先週…）
    
    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(weeks=week_number)
    end_of_week = start_of_week + timedelta(days=6)

    logs_list = AttendanceLog.objects.filter(
        user=request.user, timestamp__date__range=[start_of_week, end_of_week]
    ).order_by('timestamp')

    # 出退勤ペアの作成
    paired_sessions = []
    current_in = None
    for log in logs_list:
        if log.type == 'in':
            current_in = log.timestamp
        elif log.type == 'out' and current_in:
            paired_sessions.append((current_in, log.timestamp))
            current_in = None

    # 曜日ごとの累積時間と勤務時間帯
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekly_minutes = defaultdict(int)
    presence_distribution = {day: [] for day in weekdays}

    for start, end in paired_sessions:
        weekday = weekdays[start.weekday()]
        duration = int((end - start).total_seconds() // 60)
        weekly_minutes[weekday] += duration

        start_hour = round(start.hour + start.minute / 60, 2)
        end_hour = round(end.hour + end.minute / 60, 2)
        presence_distribution[weekday].append([start_hour, end_hour])

    # ページネーション適用（1ページ10件）
    paginator = Paginator(logs_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_minutes = sum(weekly_minutes.values())
    remaining_minutes = max(0, 2400 - total_minutes)  # 2400分 = 40時間

    return render(request, 'attendance/history.html', {
        'page_obj': page_obj,
        'week_number': week_number,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'weekly_labels': list(weekly_minutes.keys()),
        'weekly_data': list(weekly_minutes.values()),
        'presence_distribution': presence_distribution,
        'total_minutes': total_minutes,
        'remaining_minutes': remaining_minutes,
    })


@login_required
def dashboard_view(request):
    week_number = int(request.GET.get('week', 0))  # 週番号（0: 今週、1: 先週…）
    
    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(weeks=week_number)
    end_of_week = start_of_week + timedelta(days=6)

    logs_list = AttendanceLog.objects.filter(
        user=request.user, timestamp__date__range=[start_of_week, end_of_week]
    ).order_by('timestamp')

    # 出退勤ペアの作成
    paired_sessions = []
    current_in = None
    for log in logs_list:
        if log.type == 'in':
            current_in = log.timestamp
        elif log.type == 'out' and current_in:
            paired_sessions.append((current_in, log.timestamp))
            current_in = None

    # 曜日ごとの累積時間と勤務時間帯
    weekdays = ['月', '火', '水', '木', '金', '土', '日']
    weekly_minutes = defaultdict(int)
    presence_distribution = {day: [] for day in weekdays}

    for start, end in paired_sessions:
        weekday = weekdays[start.weekday()]
        duration = int((end - start).total_seconds() // 60)
        weekly_minutes[weekday] += duration

        start_hour = round(start.hour + start.minute / 60, 2)
        end_hour = round(end.hour + end.minute / 60, 2)
        presence_distribution[weekday].append([start_hour, end_hour])

    # ページネーション適用（1ページ10件）
    paginator = Paginator(logs_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_minutes = sum(weekly_minutes.values())
    remaining_minutes = max(0, 2400 - total_minutes)  # 2400分 = 40時間

    return render(request, 'attendance/dashboard.html', {
        'page_obj': page_obj,
        'week_number': week_number,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'weekly_labels': list(weekly_minutes.keys()),
        'weekly_data': list(weekly_minutes.values()),
        'presence_distribution': presence_distribution,
        'total_minutes': total_minutes,
        'remaining_minutes': remaining_minutes,
    })


def logout_and_redirect_to_top(request):
    logout(request)
    return redirect('top')  # 打刻画面にリダイレクト


# 新しく追加したランキング機能
def ranking_view(request):
    # 週番号のパラメータを取得（デフォルト: 0=今週）
    week_number = int(request.GET.get('week', 0))
    
    # 今日の日付
    today = datetime.today().date()
    
    # 指定された週の開始日と終了日を計算
    start_of_week = today - timedelta(days=today.weekday()) - timedelta(weeks=week_number)
    end_of_week = start_of_week + timedelta(days=6)
    
    # 開始日時と終了日時（時間も含める）- timezone.make_aware()を使わない
    start_datetime = datetime.combine(start_of_week, datetime.min.time())
    end_datetime = datetime.combine(end_of_week, datetime.max.time())
    
    # ユーザーごとの労働時間を計算
    users_work_time = defaultdict(int)
    
    # 各ユーザーの出勤・退勤ペアを取得
    attendance_logs = AttendanceLog.objects.filter(
        timestamp__range=(start_datetime, end_datetime)
    ).order_by('user', 'timestamp')
    
    # ユーザーIDと日付ごとにログをグループ化
    user_date_logs = defaultdict(list)
    for log in attendance_logs:
        user_id = log.user.id
        log_date = log.timestamp.date()
        user_date_logs[(user_id, log_date)].append(log)
    
    # 各ユーザーの日ごとの勤務時間を計算
    for (user_id, log_date), logs in user_date_logs.items():
        logs_sorted = sorted(logs, key=lambda x: x.timestamp)
        
        # 出勤と退勤のペアを見つける
        i = 0
        while i < len(logs_sorted) - 1:
            if logs_sorted[i].type == 'in' and logs_sorted[i+1].type == 'out':
                # 勤務時間を分単位で計算
                time_diff = logs_sorted[i+1].timestamp - logs_sorted[i].timestamp
                minutes = time_diff.total_seconds() / 60
                users_work_time[user_id] += minutes
                i += 2
            else:
                i += 1
    
    # ユーザー情報と合計時間のリストを作成
    ranking_data = []
    for user_id, total_minutes in users_work_time.items():
        try:
            user = User.objects.get(id=user_id)
            ranking_data.append({
                'username': user.username,
                'total_minutes': total_minutes,
                'total_hours': total_minutes / 60
            })
        except User.DoesNotExist:
            continue
    
    # 労働時間の降順でソート
    ranking_data.sort(key=lambda x: x['total_minutes'], reverse=True)
    
    # 大阪の天気情報を取得
    weather_info = get_osaka_weather()
    
    # 天気に基づいてclass名を設定
    weather_text = weather_info['today']['weather']
    weather_code = weather_info['today']['weather_code']
    
    # 夜間判定
    now = datetime.now()
    is_night = now.hour >= 18 or now.hour < 6
    
    # 天気クラスを設定
    weather_class = 'weather-sunny-clear'  # デフォルト
    
    if is_night:
        weather_class = 'weather-night'
    elif '雨' in weather_text or weather_code.startswith('3') or weather_code.startswith('4'):
        weather_class = 'weather-rainy'
    elif '雪' in weather_text or weather_code.startswith('6') or weather_code.startswith('7'):
        weather_class = 'weather-snowy'
    elif '曇' in weather_text or weather_code.startswith('2'):
        weather_class = 'weather-cloudy'
    elif ('晴' in weather_text and '曇' in weather_text) or weather_code.startswith('11'):
        weather_class = 'weather-sunny-cloud'
    elif '雷' in weather_text or weather_code.startswith('8'):
        weather_class = 'weather-thunder'
    elif '晴' in weather_text and '曇' not in weather_text or weather_code.startswith('10'):
        weather_class = 'weather-sunny-clear'
    
    context = {
        'ranking_users': ranking_data,
        'start_of_week': start_of_week.strftime('%Y/%m/%d'),
        'end_of_week': end_of_week.strftime('%Y/%m/%d'),
        'week_number': week_number,
        'weather_info': weather_info,
        'weather_class': weather_class,
    }
    
    return render(request, 'attendance/ranking.html', context)