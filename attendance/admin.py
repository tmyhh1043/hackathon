from django.contrib import admin
from .models import AttendanceLog

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'timestamp')
    list_filter = ('type', 'timestamp')
    search_fields = ('user__username',)
