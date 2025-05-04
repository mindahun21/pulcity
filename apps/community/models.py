from django.db import models
from apps.event.models import Event
from apps.user.models import CustomUser

class Community(models.Model):
  event = models.OneToOneField(Event,on_delete=models.CASCADE, related_name="community")
  name= models.CharField(max_length=255)
  description = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  
  def __str__(self):
    return f"Community group for event \'{self.event.title}\' id: {self.event.id},  "
  
class UserCommunity(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="communities")
  community =models.ForeignKey(Community, on_delete=models.CASCADE, related_name="users")
  joined_at = models.DateTimeField(auto_now_add=True)
  
  def __str__(self):
    return f"Usercommuniity for user:{self.user.username} and community:{self.community.name}."