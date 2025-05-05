from rest_framework import(
  viewsets,
  permissions,
)
from rest_framework.response import Response
from apps.event.serializers import EventSerializer
from apps.event.models import Event, Ticket
from apps.event.ticket.serializers import TicketSerializer
from commons.permisions import IsOrganization
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action


@extend_schema(tags=["Event management"])
class EventViewSet(viewsets.ModelViewSet):
  serializer_class = EventSerializer
  permission_classes = [permissions.IsAuthenticated, IsOrganization]
  lookup_field = 'id'
  
  def get_queryset(self):
    return Event.objects.all()
  
  @extend_schema(
    description="Retreve all tickets for Event specified by the parameter id.",
    responses=TicketSerializer(many=True)
  )
  @action(detail=True, methods=['get'])
  def tickets(self, request, id=None):
    event = self.get_object()
    tickets = Ticket.objects.filter(event=event)
    serializer = TicketSerializer(tickets,many=True)
    return Response({"tickets": serializer.data})
    
  
  
  
# TODO: get event tickets
  
  
  