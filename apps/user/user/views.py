from rest_framework import (
  viewsets,
  permissions,
  status,
)
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.user.serializers import UserSerializer
from apps.user.models import CustomUser
from ..utils import ResponsePagination


class UserViewSet(viewsets.ModelViewSet):
  serializer_class = [UserSerializer]
  permission_classes = [permissions.IsAuthenticated]
  lookup_field = 'id'
  
  def get_queryset(self):
    return CustomUser.objects.all()
  
  @action(detail=False,methods=['get'],url_path='me/following')
  def following(self, request):
    paginator = ResponsePagination()
    followings = request.user.following.all()
    paginated_followings = paginator.paginate_queryset(followings, request)
    serialized_followings = UserSerializer([f.followed for f in paginated_followings], many=True)
    
    return paginator.get_paginated_response(
      serialized_followings.data
    )
  
     
  def list(self, request):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  def create(self, request):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  def retrieve(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  def update(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  def partial_update(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  def destroy(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)