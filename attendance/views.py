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

'''
@login_required
def history_view(request):
    logs = AttendanceLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'attendance/history.html', {'logs': logs})
'''
@login_required
def history_view(request):
    if request.user.is_staff: # 管理者アカウントでは全ユーザーの履歴を表示
        logs_list = AttendanceLog.objects.all().order_by('-timestamp')  # ユーザーの勤怠記録を取得
    else: # 一般アカウントでは自分の履歴のみ
        logs_list = AttendanceLog.objects.filter(user=request.user).order_by('-timestamp')  # ユーザーの勤怠記録を取得
    
    paginator = Paginator(logs_list, 10)  # 1ページあたり10件のログを表示
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)  # 指定ページのデータを取得
    
    return render(request, 'attendance/history.html', {'page_obj': page_obj})


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