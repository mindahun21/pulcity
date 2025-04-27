from rest_framework import(
  viewsets,
  permissions,
)

from apps.event.serializers import EventSerializer
from apps.event.models import Event
from commons.permisions import IsOrganization



class EventViewSet(viewsets.ModelViewSet):
  serializer_class = EventSerializer
  permission_classes = [permissions.IsAuthenticated, IsOrganization]
  lookup_field = 'id'
  
  def get_queryset(self):
    return Event.objects.all()
  
  
  
  
  