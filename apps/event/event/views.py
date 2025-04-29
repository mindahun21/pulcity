from rest_framework import(
  viewsets,
  permissions,
)

from apps.event.serializers import EventSerializer
from apps.event.models import Event
from commons.permisions import IsOrganization
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Event management"])
class EventViewSet(viewsets.ModelViewSet):
  serializer_class = EventSerializer
  permission_classes = [permissions.IsAuthenticated, IsOrganization]
  lookup_field = 'id'
  
  def get_queryset(self):
    return Event.objects.all()
  
  
  
  
  