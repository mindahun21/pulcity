from rest_framework import serializers
from apps.event.models import Ticket

class TicketItemSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class PaymentInitiateSerializer(serializers.Serializer):
    tickets = TicketItemSerializer(many=True)

    def validate(self, data):
        items = data['tickets']
        ticket_ids = [item['ticket_id'] for item in items]
        tickets = Ticket.objects.filter(id__in=ticket_ids)

        found_ticket_ids = set(tickets.values_list('id', flat=True))
        missing_ids = [tid for tid in ticket_ids if tid not in found_ticket_ids]

        if missing_ids:
            raise serializers.ValidationError({
                'tickets': [f"Ticket(s) not found with ID(s): {', '.join(map(str, missing_ids))}"]
            })

        # Validate all tickets are from the same event
        event_ids = set(ticket.event_id for ticket in tickets)
        if len(event_ids) > 1:
            raise serializers.ValidationError("All tickets must belong to the same event.")
        
        return data

  
class OnsitePaymentserializer(serializers.Serializer):
  add_to_community = serializers.BooleanField(default=False)
  tickets = TicketItemSerializer(many=True)

  def validate(self, data):
      items = data['tickets']
      ticket_ids = [item['ticket_id'] for item in items]
      tickets = Ticket.objects.filter(id__in=ticket_ids)

      found_ticket_ids = set(tickets.values_list('id', flat=True))
      missing_ids = [tid for tid in ticket_ids if tid not in found_ticket_ids]

      if missing_ids:
          raise serializers.ValidationError({
              'tickets': [f"Ticket(s) not found with ID(s): {', '.join(map(str, missing_ids))}"]
          })

      # Validate all tickets are from the same event
      event_ids = set(ticket.event_id for ticket in tickets)
      if len(event_ids) > 1:
          raise serializers.ValidationError("All tickets must belong to the same event.")
      
      return data

class PaymentVerifySerializer(serializers.Serializer):
  tx_ref = serializers.CharField(max_length=255)
  


# response serializers for documentations

class ChapaHostedLinkDataSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()

class ChapaHostedLinkDetailSerializer(serializers.Serializer):
    message = serializers.CharField()
    status = serializers.CharField()
    data = ChapaHostedLinkDataSerializer()

class ChapaHostedLinkResponseSerializer(serializers.Serializer):
    detail = ChapaHostedLinkDetailSerializer()
    tx_ref = serializers.CharField()
    


class PaymentCustomizationSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.URLField(allow_null=True)


class PaymentDetailDataSerializer(serializers.Serializer):
    first_name = serializers.CharField(allow_null=True)
    last_name = serializers.CharField(allow_null=True)
    email = serializers.EmailField()
    phone_number = serializers.CharField(allow_null=True)
    currency = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    charge = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    mode = serializers.CharField()
    method = serializers.CharField(allow_null=True)
    type = serializers.CharField()
    status = serializers.CharField()
    reference = serializers.CharField(allow_null=True)
    tx_ref = serializers.CharField()
    customization = PaymentCustomizationSerializer()
    meta = serializers.JSONField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class PaymentDetailResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    status = serializers.CharField()
    data = PaymentDetailDataSerializer()