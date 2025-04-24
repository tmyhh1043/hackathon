
# attendance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog
from django.contrib.auth import logout
from django.core.paginator import Paginator
from .weather import get_osaka_weather
from django.utils import timezone
from django.contrib import messages
from datetime import  date
from collections import defaultdict
from datetime import timedelta


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


from django.core.paginator import Paginator
from django.shortcuts import render
from .models import AttendanceLog
from datetime import datetime, timedelta
from collections import defaultdict

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
    
    
def logout_and_redirect_to_top(request):
    logout(request)
    return redirect('top')  # 打刻画面にリダイレクト
