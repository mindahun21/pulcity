from django.urls import path
from .views import InitiatePaymentView, VerifyPaymentView, ChapaWebhookView

urlpatterns = [
  path('initiate/', InitiatePaymentView.as_view(), name="payment-initiate"),
  path('verify/',VerifyPaymentView.as_view(), name="payment-verify"),
  path('secure/chapa/webhook/',ChapaWebhookView.as_view(), name="chapa-webhook"),
]