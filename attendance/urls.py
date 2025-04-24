# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.top_view, name='top'),
    path('history/', views.history_view, name='history'),
    # ダッシュボード用URL
    path('dashboard/', views.dashboard_view, name="dashboard"),
    # ログイン画面
    path('record_after_login/<str:direction>', views.record_and_redirect, name='record_after_login'),
    # 履歴を残し、自動でtop画面に遷移
    path('record_done/', views.record_done, name='record_done'),
    # 履歴を残し、自動でtop画面に遷移
    path('record_attend/', views.record_attend, name='record_attend'),
    # 履歴を残し、自動でtop画面に遷移
    path('record_leave/', views.record_leave, name='record_leave'),
    # ログアウト状態にしてtop画面に遷移
    path('logout_to_top/', views.logout_and_redirect_to_top, name='logout_to_top'),
]