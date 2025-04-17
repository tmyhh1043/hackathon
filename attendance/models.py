from django.db import models
from django.contrib.auth.models import User

class AttendanceLog(models.Model):
    TYPE_CHOICES = [
        ('in', '出勤'),
        ('out', '退勤'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

