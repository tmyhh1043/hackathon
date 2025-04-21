# attendance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog
from django.contrib.auth import logout
from .weather import get_osaka_weather
from django.utils import timezone
from django.contrib import messages
from datetime import  date


def top_view(request):
    # 大阪の天気情報を取得
    weather_info = get_osaka_weather()
    
    # 既存の処理と統合
    return render(request, 'attendance/top.html', {
        'weather_info': weather_info
    })

@login_required
def history_view(request):
    logs = AttendanceLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'attendance/history.html', {'logs': logs})


def dashboard_view(request):
    return render(request, 'attendance/dashboard.html')

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
        
        AttendanceLog.objects.create(
            user=request.user,
            type='in',
            timestamp=timezone.now()
        )
    
    elif direction == "out":
        already_clocked_out = AttendanceLog.objects.filter(
            user=request.user,
            type='out',
            timestamp__date=today
        ).exists()

        if already_clocked_out:
            return redirect('record_leave') 

        # 出勤ログを保存
        AttendanceLog.objects.create(
            user=request.user,
            type='out',
            timestamp=timezone.now()
        )
        
    return redirect('record_done')

@login_required
def record_done(request):
    logout(request)
    return render(request, 'attendance/record_done.html')

@login_required
def record_attend(request):
    logout(request)
    return render(request, 'attendance/record_attend.html')

@login_required
def record_leave(request):
    logout(request)
    return render(request, 'attendance/record_leave.html')


from collections import defaultdict
from datetime import timedelta

@login_required
def history_view(request):
    logs = AttendanceLog.objects.filter(user=request.user).order_by('timestamp')

    # 出退勤のペア作成
    paired_sessions = []
    current_in = None
    for log in logs:
        if log.type == 'in':
            current_in = log.timestamp
        elif log.type == 'out' and current_in:
            paired_sessions.append((current_in, log.timestamp))
            current_in = None

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

    # 円グラフ用：学習済み合計時間と残り時間
    total_minutes = sum(weekly_minutes.values())
    remaining_minutes = max(0, 2400 - total_minutes)  # 2400分 = 40時間

    return render(request, 'attendance/history.html', {
        'logs': logs,
        'weekly_labels': list(weekly_minutes.keys()),
        'weekly_data': list(weekly_minutes.values()),
        'presence_distribution': presence_distribution,
        'total_minutes': total_minutes,
        'remaining_minutes': remaining_minutes,
    })
