from rest_framework import (
  serializers,
)
from apps.event.models import UserTicket

class ScanSerializer(serializers.Serializer):
    user_ticket_id = serializers.IntegerField()
    event_id = serializers.IntegerField()

    def validate(self, data):
        user_ticket_id = data.get('user_ticket_id')
        event_id = data.get('event_id')

        try:
            user_ticket = UserTicket.objects.select_related('ticket__event').get(id=user_ticket_id, used=False)
        except UserTicket.DoesNotExist:
            raise serializers.ValidationError("Invalid or already used ticket.")

        if user_ticket.ticket.event.id != event_id:
            raise serializers.ValidationError("Ticket does not belong to this event.")

        data['user_ticket'] = user_ticket
        data['event'] = user_ticket.ticket.event
        return data