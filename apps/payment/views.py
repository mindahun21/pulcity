import time
import random
import httpx
from chapa import Chapa
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings

from .models import Payment
from .serializers import (
  PaymentInitiateSerializer, 
  PaymentVerifySerializer,
  ChapaHostedLinkResponseSerializer,
  PaymentDetailResponseSerializer,
)
from apps.event.models import Ticket
from drf_spectacular.utils import extend_schema




chapa = Chapa(settings.CHAPA_SECRET)

@extend_schema(tags=["Payment"])
class InitiatePaymentView(APIView):
  serializer_class = PaymentInitiateSerializer
  
  @extend_schema(
        request=PaymentInitiateSerializer,
        responses={200: ChapaHostedLinkResponseSerializer},
    )
  def post(self, request):
      serializer = self.serializer_class(data=request.data)
      serializer.is_valid(raise_exception=True)

      ticket_id = serializer.validated_data['ticket_id'] 

      # generate unique tx_ref
      tx_ref = f"pulcity-{request.user.id}-{ticket_id}-{int(time.time())}{random.randint(1000, 9999)}"
      
      try:
        ticket = Ticket.objects.get(id=ticket_id)
      except Ticket.DoesNotExist:
          return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
      
      data = {
        "tx_ref":tx_ref,
        "amount":float(ticket.price),
        "currency":"ETB",
        "email":request.user.email,
        "first_name":request.user.first_name,
        "last_name":request.user.last_name,
        "callback_url":"http://localhost:5173/account/verified",
        "return_url":"http://localhost:5173/account/verified",
        'customization': {
          'title': 'Event Payment',
          'description': 'Payment for Pulcity event ticket',
        }
      }
      
      response = chapa.initialize(**data)

      if response.get("status") != "success":
        return Response({"detail":"Failed to initialize payment"})
      
      Payment.objects.create(
          user=request.user,
          ticket=ticket,
          tx_ref=tx_ref,
          currency="ETB",
          amount=ticket.price,
          payment_title="Event Payment",
          description="Payment for Pulcity event ticket",
          status='pending'
      )
      return Response({"detail":response,"tx_ref":tx_ref})


@extend_schema(tags=["Payment"])
class VerifyPaymentView(APIView):
  serializer_class = PaymentVerifySerializer
  
  @extend_schema(
      request=PaymentVerifySerializer,
      responses={200: PaymentDetailResponseSerializer},
  )
  def post(self, request):
    serializer = self.serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    tx_ref=serializer.validated_data['tx_ref']
    try:
      payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
      return Response({"detail":f"No payment initialized with tx_ref = {tx_ref} "})
    
    # response = chapa.verify(tx_ref)
    headers = {"Authorization": f"Bearer {settings.CHAPA_SECRET}"}
    url = f"https://api.chapa.co/v1/transaction/verify/{tx_ref}"

    response = httpx.get(url, headers=headers).json()
    
    if response['status'] != "success":
      payment.status = "success"
      payment.save()
    
    return Response(response)