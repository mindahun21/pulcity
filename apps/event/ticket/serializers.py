from rest_framework import serializers
from apps.event.models import Ticket, Event

class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = [
            'id',          
            'event', 
            'name',
            'price',
            'valid_from',
            'valid_until',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value

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
    
