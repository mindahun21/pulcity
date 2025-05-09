from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event
from apps.notification.models import Notification
import logging
from apps.user.models import CustomUser

logger = logging.getLogger('django')

@receiver(post_save, sender=Event)
def notify_followers_on_new_event(sender, instance, created, **kwargs):
    if created:
        organizer = instance.organizer
        follower_users = CustomUser.objects.filter(following__followed=organizer)
        for follower in follower_users:
            Notification.objects.create(
                user=follower,
                message=f"{organizer.profile.name} has created a new event: {instance.title}",
                event=instance
            )