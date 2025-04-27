from rest_framework import (
  viewsets,
  status,
  permissions
)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from apps.user.serializers import UserSerializer
from apps.user.models import CustomUser
from ..utils import ResponsePagination


class OrganizationViewSet(viewsets.ModelViewSet):
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field ='id'   
  
  def get_queryset(self):
    return CustomUser.objects.filter(role='organization')
  
  @action(detail=True, methods=['post'])
  def follow(self, request, id=None):
      user_to_follow = self.get_object()
      if request.user.is_following(user_to_follow):
        return Response({'detail':"Already followed!"},status=status.HTTP_400_BAD_REQUEST)
      request.user.follow(user_to_follow)
      return Response({"detail": "following"})

  @action(detail=True, methods=['post'])
  def unfollow(self, request, id=None):
      user_to_unfollow = self.get_object()
      if request.user.is_following(user_to_unfollow):
        request.user.unfollow(user_to_unfollow)
        return Response({"detail": "unfollowed"})
      
      return Response({"detail": "Already not followed"}, status=status.HTTP_400_BAD_REQUEST)
    
  @action(detail=True,methods=['get'])
  def followers(self, request,id=None):
    paginator = ResponsePagination()
    org = self.get_object()
    followers = org.followers.all()
    paginated_followers = paginator.paginate_queryset(followers, request)
    serialized_followers = UserSerializer([f.follower for f in paginated_followers], many=True)
    
    return paginator.get_paginated_response(
      serialized_followers.data
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