from django.urls import path
from .views import InitiatePaymentView, VerifyPaymentView, ChapaWebhookView,ChapaCallbackView,ChapaReturnView

urlpatterns = [
  path('initiate/', InitiatePaymentView.as_view(), name="payment-initiate"),
  path('verify/',VerifyPaymentView.as_view(), name="payment-verify"),
  path('secure/chapa/webhook/',ChapaWebhookView.as_view(), name="chapa-webhook"),
  # path('callback/<str:tx_ref>/', ChapaCallbackView.as_view(), name='chapa-callback'),
  path('return/<str:event_id>/<str:tx_ref>/', ChapaReturnView.as_view(), name='chapa-return'),

]