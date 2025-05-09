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
from apps.event.models import Bookmark
from apps.event.serializers import EventSerializer

@extend_schema(tags=["user management"])
class UserViewSet(viewsets.ModelViewSet):
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field = 'id'
  
  def get_queryset(self):
    return CustomUser.objects.all()
  
  @extend_schema(
    request=None,
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
  
  @extend_schema(
    request=None,
    description="retreve the list of events bookmarked by currently authenticated user.",
    responses=EventSerializer(many=True)
  )
  @action(detail=False,methods=['get'],url_path="me/bookmarks")
  def bookmarks(self, request):
    user = request.user
    bookmarks = Bookmark.objects.filter(user=user)
    paginator = ResponsePagination()
    paginated_bookmarks = paginator.paginate_queryset(bookmarks, request)
    serialized_bookmarks = EventSerializer([bookmark.event for bookmark in paginated_bookmarks], context={'request':request}, many=True)
    
    return paginator.get_paginated_response(
      serialized_bookmarks.data
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