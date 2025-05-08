from rest_framework import serializers
from .models import Notification
from apps.event.serializers import EventSerializer
from drf_spectacular.utils import extend_schema_field

class NotificationSerializer(serializers.ModelSerializer):
  event = serializers.SerializerMethodField()
  class Meta:
    model = Notification
    fields= ['id','user','event', 'message','read','sent_at', 'created_at']
    read_only_fields = ['id','user','read','sent_at', 'created_at']
    
  @extend_schema_field(EventSerializer)
  def get_event(self, obj):
    request = self.context.get('request')
    return EventSerializer(obj.event, context={'request':request}).data
  
  
  