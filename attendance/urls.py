# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.top_view, name='top'),
    path('history/', views.history_view, name='history'),
    path('record/<str:type>/', views.record_attendance, name='record_attendance'),
    # ダッシュボード用URL
    path('dashboard/', views.dashboard_view, name="dashboard")
]