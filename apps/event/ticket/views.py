from rest_framework import(
  viewsets,
  permissions,
  status,
  serializers,
)
from rest_framework.exceptions import PermissionDenied
from apps.event.models import Ticket, UserTicket
from apps.community.models import UserCommunity
from apps.payment.models import Payment, PaymentItem
from apps.payment.serializers import OnsitePaymentserializer
from apps.event.ticket.serializers import TicketSerializer
from commons.permisions import IsOrganization
from commons.utils import ResponsePagination
from drf_spectacular.utils import extend_schema,OpenApiResponse,inline_serializer
from rest_framework.decorators import action
from rest_framework.response import Response


@extend_schema(tags=["Ticket management"])
class TicketViewSet(viewsets.ModelViewSet):
  serializer_class = TicketSerializer
  lookup_field = 'id'
  
  
  def get_queryset(self):
    return Ticket.objects.all()
  
  def get_permissions(self):
    if self.action in ['list','retrieve','onsite_payment','bought']:
      return [permissions.IsAuthenticated()]
    return [permissions.IsAuthenticated(), IsOrganization()]

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
    
  @extend_schema(
    description="registering onsite payment to database and add user to event community if payload add_to_community set to True",
    request=OnsitePaymentserializer(),
    responses={
      200:OpenApiResponse(
        inline_serializer(
          name="OnsitePaymentSuccess",
          fields={"detail":serializers.CharField(),}
        )
      ),
      400:OpenApiResponse(
        inline_serializer(
          name="ErrorResponse",
          fields={"detail":serializers.CharField(),}
        )
      )
    }
  )
  @action(detail=False, methods=['post'], url_path='payment/onsite')
  def onsite_payment(self, request, id=None):
    serializer = OnsitePaymentserializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    add_to_community = serializer.validated_data['add_to_community']
    items_data = serializer.validated_data['tickets']
    ticket_ids = [item['ticket_id'] for item in items_data]
    tickets = Ticket.objects.filter(id__in=ticket_ids)
    ticket_map = {t.id: t for t in tickets}
    
    total_amount = sum(ticket_map[item['ticket_id']].price * item['quantity'] for item in items_data)
    event = ticket_map[items_data[0]['ticket_id']].event
    
    
    payment = Payment.objects.create(
        user=request.user,
        currency="ETB",
        amount=total_amount,
        payment_title="Event Payment",
        description="Payment for Pulcity event ticket",
        status='success'
    )
    for item in items_data:
      paymentItem = PaymentItem.objects.create(
          payment=payment,
          ticket=ticket_map[item['ticket_id']],
          quantity=item['quantity'],
          unit_price=ticket_map[item['ticket_id']].price
      )
      for _ in range(item['quantity']):
        UserTicket.objects.create(user=payment.user, ticket=paymentItem.ticket)
    
    if hasattr(event, 'community') and add_to_community:
      UserCommunity.objects.get_or_create(user=payment.user, community=event.community)

    
    return Response({"detail":"Payment successful."}, status=status.HTTP_200_OK)

  @extend_schema(
    request=None,
    description="retrieve the list of tickets bought by currently authenticated user.",
    responses=TicketSerializer(many=True)
  )
  @action(detail=False, methods=['get'])
  def bought(self, request):
    user = request.user
    user_tickets = UserTicket.objects.filter(user=user).select_related('ticket')

    ticket_ids = user_tickets.values_list('ticket_id', flat=True).distinct()
    tickets = Ticket.objects.filter(id__in=ticket_ids)

    paginator = ResponsePagination()
    paginated_tickets = paginator.paginate_queryset(tickets, request)
    serialized = TicketSerializer(paginated_tickets, many=True, context={'request': request})
    
    return paginator.get_paginated_response(
      serialized.data
    )    



