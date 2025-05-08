from django.db import models
from apps.user.models import CustomUser
from apps.event.models import Event

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications')
    read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
