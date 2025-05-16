from django.db import models
from django.conf import settings
from apps.event.models import Ticket

class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tickets = models.ManyToManyField(
        Ticket,
        through="PaymentItem",
        related_name="payments",
    )
    # ticket = models.ForeignKey(Ticket, related_name='single_payments', on_delete=models.CASCADE) 
    tx_ref = models.CharField(max_length=255, unique=True, null=True, blank=True)
    method = models.CharField(max_length=20,choices=[('online','ONLINE'),('onsite','ONSITE')], default='online')
    currency = models.CharField(max_length=10,default="ETB")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_title = models.CharField(max_length=255,blank=True,null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(choices=[('created', 'CREATED'), ('pending', 'PENDING'), ('success', 'SUCCESS'), ('failed', 'FAILED')], default='created', max_length=50)
    response_dump= models.JSONField(blank=True, default=dict)
    def __str__(self):
        return f"{self.user.email} - {self.ticket.id} - {self.tx_ref}"

class PaymentItem(models.Model):
    payment = models.ForeignKey("Payment", on_delete=models.CASCADE, related_name="items")
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  

    def get_total_price(self):
        return self.unit_price * self.quantity
