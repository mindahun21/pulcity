from rest_framework import (
  serializers,
)
from apps.event.models import Event
from apps.event.serializers import EventSerializer
from apps.user.models import CustomUser
from .models import Community
from drf_spectacular.utils import extend_schema_field

class AddUserToCommunitySerializer(serializers.Serializer):
  user_id = serializers.IntegerField(help_text="ID of the user to be added to the community")
  event_id = serializers.IntegerField(help_text="ID of the event associated with the community")
  
  def validate_user_id(self, value):
      """Check if the user with the given ID exists."""
      if not CustomUser.objects.filter(id=value).exists():
          raise serializers.ValidationError("User with this ID does not exist.")
      return value

  def validate_event_id(self, value):
      """Check if the event with the given ID exists."""
      if not Event.objects.filter(id=value).exists():
          raise serializers.ValidationError("Event with this ID does not exist.")
      return value
    
    
class CommunitySerializer(serializers.ModelSerializer):
  event = serializers.SerializerMethodField()
  class Meta:
    model =Community
    fields = [
      'id', 'event','name','description','created_at','updated_at'
    ]
    read_only_fields = ['id','created_at','updated_at']

  @extend_schema_field(EventSerializer)
  def get_event(self, obj):
    request = self.context.get('request')
    return EventSerializer(obj.event, context={'request':request}).data
  
  
  