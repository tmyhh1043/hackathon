# attendance/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import AttendanceLog
from django.contrib.auth import logout

from django.core.paginator import Paginator


@login_required
def top_view(request):
    return render(request, 'attendance/top.html')

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

@login_required
def record_attendance(request, type):
    if type in ['in', 'out']:
        AttendanceLog.objects.create(user=request.user, type=type)
    return redirect('history')  # 登録後は履歴ページへリダイレクト

@login_required
def dashboard_view(request, type):
    return render(request, 'attendance/dashboard.html')  
