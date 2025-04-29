from rest_framework import(
  viewsets,
  permissions,
)
from rest_framework.exceptions import PermissionDenied
from apps.event.models import Ticket
from apps.event.ticket.serializers import TicketSerializer
from commons.permisions import IsOrganization
from drf_spectacular.utils import extend_schema


@extend_schema(tags=["Ticket management"])
class TicketViewSet(viewsets.ModelViewSet):
  serializer_class = TicketSerializer
  permission_classes = [permissions.IsAuthenticated, IsOrganization]
  lookup_field = 'id'
  
  
  def get_queryset(self):
    return Ticket.objects.all()

  def perform_update(self, serializer):
    # Ensure only the owner organization can update
    if serializer.instance.event.organizer != self.request.user:
        raise PermissionDenied("You do not have permission to update this ticket.")
    serializer.save()

  def perform_destroy(self, instance):
    # Ensure only the owner organization can delete
    if instance.event.organizer != self.request.user:
        raise PermissionDenied("You do not have permission to delete this ticket.")
    instance.delete()