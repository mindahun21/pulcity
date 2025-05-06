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

from .models import Payment
from .serializers import (
  PaymentInitiateSerializer, 
  PaymentVerifySerializer,
  ChapaHostedLinkResponseSerializer,
  PaymentDetailResponseSerializer,
)
from apps.event.models import Ticket, UserTicket
from apps.community.models import Community, UserCommunity
from drf_spectacular.utils import extend_schema




chapa = Chapa(settings.CHAPA_SECRET)
logger = logging.getLogger('django')

def custom_verify_webhook(secret_key: str, raw_body: bytes, chapa_signature: str) -> bool:
    signature = hmac.new(secret_key.encode(), raw_body, hashlib.sha256).hexdigest()
    
    logger.info(f"Chapa Signature Header: {chapa_signature}")
    logger.info(f":CHAPA_SECRET_HASH {secret_key}")
    logger.info(f"Calculated Signature:   {signature}")
    logger.info(f"Raw Body: {raw_body.decode(errors='replace')}")
    return signature == chapa_signature


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
        "callback_url":settings.CHAPA_CALLBACK_URL,
        "return_url":settings.CHAPA_RETURN_URL,
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

    try:
      response = httpx.get(url, headers=headers)
      chapa_data = response.json()
    except Exception as e:
        return Response({"detail": "Failed to contact Chapa."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if chapa_data.get('status') != "success":
      return Response(chapa_data, status=status.HTTP_400_BAD_REQUEST)
    
    payment.status = "success"
    payment.save()
    
    UserTicket.objects.get_or_create(user=payment.user, ticket=payment.ticket)
    if hasattr(payment.ticket.event, 'community'):
      community = payment.ticket.event.community
      UserCommunity.objects.get_or_create(user=payment.user, community=community)

    return Response(chapa_data)

@extend_schema(exclude=True)
@method_decorator(csrf_exempt, name='dispatch')
class ChapaWebhookView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]
    def post(self, request):
        client_ip = request.META.get('REMOTE_ADDR')
        logger.debug(f"Webhook received from IP: {client_ip}")

        raw_body = request.body
        chapa_signature = request.headers.get("Chapa-Signature") 
        logger.info("Received Chapa webhook request.")

        if not chapa_signature:
            logger.warning("Missing Chapa-Signature in webhook request.")
            return Response({"detail": "Missing Chapa-Signature"}, status=400)
        
        if not verify_webhook(settings.CHAPA_SECRET_HASH, raw_body, chapa_signature):
            logger.error("Invalid Chapa signature for webhook.")
            return Response({"detail": "Invalid signature"}, status=400)

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook request.")
            return Response({"detail": "Invalid JSON"}, status=400)

        event = body.get("event")
        data = body.get("data", {})
        tx_ref = data.get("tx_ref")

        logger.info(f"Webhook event: {event}, tx_ref: {tx_ref}")

        if event == "charge.success" and tx_ref:
            try:
                payment = Payment.objects.get(tx_ref=tx_ref)
                logger.info(f"Found payment with tx_ref={tx_ref}")
            except Payment.DoesNotExist:
                logger.warning(f"Payment with tx_ref={tx_ref} not found.")
                return Response({"detail": "Payment not found"}, status=404)

            if payment.status != "success":
                payment.status = "success"
                payment.save()
                UserTicket.objects.get_or_create(user=payment.user, ticket=payment.ticket)
                logger.info(f"Payment marked as success and UserTicket created for user={payment.user.id}")

        return Response({"detail": "Webhook received"}, status=200)
