# attendance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog

@login_required
def top_view(request):
    return render(request, 'attendance/top.html')

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
def home_view(request):
    return render(request, 'attendance/home.html')