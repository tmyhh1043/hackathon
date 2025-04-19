# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.top_view, name='top'),
    path('history/', views.history_view, name='history'),
    path('record/<str:type>/', views.record_attendance, name='record_attendance'),
    # ダッシュボード用URL
    path('dashboard/', views.dashboard_view, name="dashboard"),
    # ログイン画面
    path('record_after_login/<str:direction>', views.record_and_redirect, name='record_after_login'),
    # 履歴を残し、自動でtop画面に遷移
    path('record_done/', views.record_done, name='record_done'),
]