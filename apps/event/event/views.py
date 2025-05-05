from rest_framework import(
  viewsets,
  permissions,
)
from rest_framework.response import Response
from apps.event.serializers import EventSerializer
from apps.event.models import Event, Ticket, UserTicket
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
  
  
  @extend_schema(
    description="Retreve all tickets a user bought for an event specified by the parameter id.",
    responses=TicketSerializer(many=True)
  )
  @action(detail=True, methods=['get'], url_path='user/tickets')
  def user_tickets(self, request, id=None):
    event = self.get_object()
    user = request.user

    user_tickets = UserTicket.objects.filter(
      user=user,
      ticket__event=event
    ).select_related('ticket')
    tickets = [ut.ticket for ut in user_tickets]
    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data)
    
    
  
  
  
# TODO: get event tickets
  
  
  