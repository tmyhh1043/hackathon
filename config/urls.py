from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('attendance.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LoginView.as_view(), name='logout'),
]