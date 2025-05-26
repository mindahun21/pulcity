from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event
from apps.notification.models import Notification
import logging
from apps.user.models import CustomUser
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger('django')

@receiver(post_save, sender=Event)
def notify_followers_on_new_event(sender, instance, created, **kwargs):
    if created:
        organizer = instance.organizer
        follower_users = CustomUser.objects.filter(following__followed=organizer).distinct()
        
        notifications = [
            Notification(user=follower, message=f"{organizer.profile.name} has created a new event: {instance.title}", event=instance)
            for follower in follower_users
        ]
        Notification.objects.bulk_create(notifications)

        channel_layer = get_channel_layer()
        for follower in follower_users:
            async_to_sync(channel_layer.group_send)(
                f"user_{follower.id}",
                {
                    "type": "notify",
                    "content": {
                        "message": f"{organizer.profile.name} has created a new event: {instance.title}",
                        "event_id": instance.id,
                        "organizer": organizer.profile.name,
                    },
                },
            )