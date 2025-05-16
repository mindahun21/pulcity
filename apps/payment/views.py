import httpx, logging, random, time, json, hmac, hashlib
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from chapa import Chapa
from chapa import verify_webhook

from .models import Payment, PaymentItem
from .serializers import (
  PaymentInitiateSerializer, 
  PaymentVerifySerializer,
  ChapaHostedLinkResponseSerializer,
  PaymentDetailResponseSerializer,
)
from apps.event.models import Ticket, UserTicket
from apps.community.models import Community, UserCommunity
from drf_spectacular.utils import extend_schema
from django.http import HttpResponse




chapa = Chapa(settings.CHAPA_SECRET)
logger = logging.getLogger('django')

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

      items_data = serializer.validated_data['tickets']
      ticket_ids = [item['ticket_id'] for item in items_data]
      tickets = Ticket.objects.filter(id__in=ticket_ids)
      ticket_map = {t.id: t for t in tickets}
      
      total_amount = sum(ticket_map[item['ticket_id']].price * item['quantity'] for item in items_data)
      event = ticket_map[items_data[0]['ticket_id']].event

      # generate unique tx_ref
      tx_ref = f"pulcity-{request.user.id}-{int(time.time())}{random.randint(1000, 9999)}"
      
      data = {
        "tx_ref":tx_ref,
        "amount":float(total_amount),
        "currency":"ETB",
        "email":request.user.email,
        "first_name":request.user.first_name,
        "last_name":request.user.last_name,
        "return_url": f"https://mindahun.pro.et/api/v1/payment/return/{event.id}/{tx_ref}",
        'customization': {
          'title': 'Event Payment',
          'description': 'Payment for Pulcity event ticket',
        }
      }
      
      response = chapa.initialize(**data)

      if response.get("status") != "success":
        return Response({"detail":"Failed to initialize payment","chapa_response":response})
      
      payment = Payment.objects.create(
          user=request.user,
          tx_ref=tx_ref,
          currency="ETB",
          amount=total_amount,
          payment_title="Event Payment",
          description="Payment for Pulcity event ticket",
          status='pending'
      )
      
      for item in items_data:
        PaymentItem.objects.create(
            payment=payment,
            ticket=ticket_map[item['ticket_id']],
            quantity=item['quantity'],
            unit_price=ticket_map[item['ticket_id']].price
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

    try:
      response = httpx.get(url, headers=headers)
      chapa_data = response.json()
    except Exception as e:
        return Response({"detail": "Failed to contact Chapa."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if chapa_data.get('status') != "success":
      return Response(chapa_data, status=status.HTTP_400_BAD_REQUEST)
    
    
    if payment.status != "success":
      payment.status = "success"
      payment.save()
      for item in payment.items.all():
        for _ in range(item.quantity):
            UserTicket.objects.create(user=payment.user, ticket=item.ticket)

        event = item.ticket.event
        if hasattr(event, 'community'):
            UserCommunity.objects.get_or_create(user=payment.user, community=event.community)

    return Response(chapa_data)
  
  
@extend_schema(exclude=True)
@method_decorator(csrf_exempt, name='dispatch')
class ChapaWebhookView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]
    def post(self, request):
        client_ip = request.META.get('REMOTE_ADDR')
        logger.info(f"Webhook received from IP: {client_ip}")

        raw_body = request.body
        chapa_signature = request.headers.get("Chapa-Signature") 
        logger.info("Received Chapa webhook request.")

        if not chapa_signature:
            logger.warning("Missing Chapa-Signature in webhook request.")
            return Response({"detail": "Missing Chapa-Signature"}, status=400)

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request.")
            return Response({"detail": "Invalid JSON"}, status=400)
        
        event = body.get("event")
        tx_ref = body.get("tx_ref")

        logger.info(f"Webhook event: {event}, tx_ref: {tx_ref}")
        if not tx_ref:
            logger.warning("Missing tx_ref in webhook data.")
            return Response({"detail": "Missing tx_ref"}, status=400)

        if event == "charge.success":
            try:
                payment = Payment.objects.get(tx_ref=tx_ref)
                logger.info(f"Found payment with tx_ref={tx_ref}")
            except Payment.DoesNotExist:
                logger.warning(f"Payment with tx_ref={tx_ref} not found.")
                return Response({"detail": "Webhook received but payment not found"}, status=200)

            if payment.status != "success":
                payment.status = "success"
                payment.save()
                for item in payment.items.all():
                  for _ in range(item.quantity):
                      UserTicket.objects.create(user=payment.user, ticket=item.ticket)

                  event = item.ticket.event
                  if hasattr(event, 'community'):
                      UserCommunity.objects.get_or_create(user=payment.user, community=event.community)

        else:
            logger.info(f"Ignoring non-successful payment event: {event}")


        return Response({"detail": "Webhook received"}, status=200)

@extend_schema(exclude=True)
class ChapaCallbackView(APIView):
  authentication_classes = [] 
  permission_classes = [AllowAny]
  
  def post(self, request, event_id):
    logger.info("Chapa callback received")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in callback")
        return Response({"detail": "Invalid JSON"}, status=400)

    event = data.get("event")
    tx_ref = data.get("data", {}).get("tx_ref")

    logger.info(f"Event: {event}, tx_ref: {tx_ref}")
    try:
      payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
      return Response({"detail":f"No payment initialized with tx_ref = {tx_ref} "})


    if event == "charge.success" and tx_ref:
        logger.info("Payment was successful")
        payment.status = "success"
        payment.save()
        
        UserTicket.objects.get_or_create(user=payment.user, ticket=payment.ticket)
        if hasattr(payment.ticket.event, 'community'):
          community = payment.ticket.event.community
          UserCommunity.objects.get_or_create(user=payment.user, community=community)

    else:
        logger.warning("Payment was not successful")

    return Response({"detail": "Callback processed"}, status=200)
  
from django.shortcuts import redirect

@extend_schema(exclude=True)
class ChapaReturnView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]

    def get(self, request, event_id, tx_ref):
        url = f'pulcity://checkout/{event_id}/{tx_ref}'
        response = HttpResponse(status=302)
        response['Location'] = url
        return response
