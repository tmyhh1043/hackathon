# attendance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog
from django.contrib.auth import logout
from .weather import get_osaka_weather


@login_required
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


@login_required
def record_attendance(request, type):
    if type in ['in', 'out']:
        AttendanceLog.objects.create(user=request.user, type=type)
    return redirect('history')  # 登録後は履歴ページへリダイレクト


@login_required
def dashboard_view(request):
    return render(request, 'attendance/dashboard.html')