from rest_framework import (
  serializers,
)
from apps.event.models import Rating
from apps.user.serializers import UserSerializer

class RatingSerializer(serializers.ModelSerializer):
  user = UserSerializer(read_only=True)
  class Meta:
    model = Rating
    fields = ['id', 'user', 'value','comment','created_at','updated_at']
    read_only_fields = ['id','user','created_at','updated_at']
    