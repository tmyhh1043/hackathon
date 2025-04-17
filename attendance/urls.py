# attendance/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('history/', views.history_view, name='history'),
    path('record/<str:type>/', views.record_attendance, name='record_attendance'),
]