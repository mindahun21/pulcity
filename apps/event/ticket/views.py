from rest_framework import(
  viewsets,
  permissions,
  status,
  serializers,
)
from rest_framework.exceptions import PermissionDenied
from apps.event.models import Ticket, UserTicket
from apps.payment.models import Payment
from apps.event.ticket.serializers import TicketSerializer, OnsitePaymentserializer
from commons.permisions import IsOrganization
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
    if self.action in ['list','retrieve','onsite_payment']:
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
  @action(detail=True, methods=['post'], url_path='payment/onsite')
  def onsite_payment(self, request, id=None):
    serializer = OnsitePaymentserializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    add_to_community = serializer.validated_data['add_to_community']
    
    ticket = self.get_object()
    event = ticket.event
    if not event.onsite_payement:
      return Response({"detail":"This event didn't accept onsite payment"}, status=status.HTTP_400_BAD_REQUEST)
    
    payment, paymentCreated = Payment.objects.get_or_create(
      user=request.user,
      ticket=ticket,
      currency="ETB",
      amount=ticket.price,
      payment_title="Event Payment",
      description="Payment for Pulcity event ticket",
      method='onsite',
      status='success',
    )
    UserTicket.objects.get_or_create(user=payment.user, ticket=payment.ticket)
    
    if add_to_community and hasattr(payment.ticket.event, 'community'):
      community = event.community 
      UserCommunity.objects.get_or_create(user=request.user, community=community)
    
    if not paymentCreated:
      return Response({"detail":"Payment already done before."}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"detail":"Payment successful."}, status=status.HTTP_200_OK)

    
