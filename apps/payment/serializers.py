from rest_framework import serializers

class PaymentInitiateSerializer(serializers.Serializer):
  ticket_id = serializers.IntegerField()
  
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