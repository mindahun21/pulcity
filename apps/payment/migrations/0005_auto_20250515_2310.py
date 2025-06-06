# Generated by Django 5.2 on 2025-05-15 23:10

from django.db import migrations

def copy_ticket_to_payment_item(apps, schema_editor):
    Payment = apps.get_model("payment", "Payment")
    PaymentItem = apps.get_model("payment", "PaymentItem")
    for payment in Payment.objects.exclude(ticket__isnull=True):
        PaymentItem.objects.create(
            payment=payment,
            ticket=payment.ticket,
            quantity=1,
            unit_price=payment.amount,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_alter_payment_ticket_paymentitem_payment_tickets'),
    ]

    operations = [
      migrations.RunPython(copy_ticket_to_payment_item),
    ]
