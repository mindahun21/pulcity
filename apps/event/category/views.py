from rest_framework import (
  viewsets,
  permissions,
)

from apps.event.serializers import CategorySerializer
from apps.event.models import Category
from commons.permisions import IsOrganization

class CategoryViewSet(viewsets.ModelViewSet):
  serializer_class = CategorySerializer
  permission_classes = [permissions.IsAuthenticated, IsOrganization]
  lookup_field = 'id'
  
  def get_queryset(self):
    return Category.objects.all()
  
