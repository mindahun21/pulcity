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
from drf_spectacular.utils import extend_schema
from ..serializers import UserWithOrganizationProfileDocSerializer


@extend_schema(tags=["user management"])
class UserViewSet(viewsets.ModelViewSet):
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field = 'id'
  
  def get_queryset(self):
    return CustomUser.objects.all()
  
  @extend_schema(
    description="retreve the list of organizations followed by currently authenticated user.",
    responses=UserWithOrganizationProfileDocSerializer(many=True)
  )
  @action(detail=False,methods=['get'],url_path='me/following')
  def following(self, request):
    paginator = ResponsePagination()
    followings = request.user.following.all()
    paginated_followings = paginator.paginate_queryset(followings, request)
    serialized_followings = UserSerializer([f.followed for f in paginated_followings], many=True, context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_followings.data
    )
  
  @extend_schema(exclude=True)
  def list(self, request):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def create(self, request):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def retrieve(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def update(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def partial_update(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def destroy(self, request, id=None):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)