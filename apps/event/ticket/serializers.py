from rest_framework import serializers
from apps.event.models import Ticket, Event, UserTicket
from drf_spectacular.utils import extend_schema_field

class TicketSerializer(serializers.ModelSerializer):
    onsite_payement=serializers.SerializerMethodField()
    class Meta:
        model = Ticket
        fields = [
            'id',          
            'event', 
            'name',
            'description',
            'price',
            'valid_from',
            'valid_until',
            'active',
            'onsite_payement',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at','onsite_payement']

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value

    @extend_schema_field(serializers.BooleanField())
    def get_onsite_payement(self, obj):
      return obj.event.onsite_payement

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value
    
    def create(self, validated_data):
        # Directly fetch the event instance based on the passed event reference
        event = validated_data.get('event')
        
        # Check if event exists and if the organizer is the correct user
        if event.organizer != self.context['request'].user:
            raise serializers.ValidationError({"event": "You do not have permission to add tickets to this event."})
        
        return Ticket.objects.create(**validated_data)
    

class UserTicketSerializer(serializers.ModelSerializer):
  ticket = TicketSerializer()
  class Meta:
    model = UserTicket
    fields = ['id','ticket', 'used', 'purchase_date']