from rest_framework import (
  serializers,
)
from apps.event.models import Rating
from apps.user.serializers import UserSerializer

class RatingSerializer(serializers.ModelSerializer):
  user = UserSerializer(read_only=True)
  class Meta:
    model = Rating
    fields = ['id', 'user', 'value','comment','created_at','updated_at']
    read_only_fields = ['id','user','created_at','updated_at']
    
    
class UserRatingSerializer(serializers.ModelSerializer):
  
  event = serializers.SerializerMethodField()
  class Meta:
    model = Rating
    fields = ['id', 'event', 'value','comment','created_at','updated_at']
    read_only_fields = ['id','event','created_at','updated_at']
    
  def get_event(self, obj):
    from apps.event.serializers import EventSerializer
    request = self.context['request']
    return EventSerializer(obj.event, context={'request': request}).data
    