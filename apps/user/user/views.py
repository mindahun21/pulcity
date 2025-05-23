from rest_framework import (
  viewsets,
  permissions,
  status,
)
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.user.serializers import UserSerializer,ProfileSerializer
from apps.user.models import CustomUser, Profile
from ..utils import ResponsePagination
from drf_spectacular.utils import extend_schema
from ..serializers import UserWithOrganizationProfileDocSerializer
from apps.event.models import Bookmark, Rating
from apps.event.serializers import EventSerializer
from apps.event.rating.serializers import UserRatingSerializer
@extend_schema(tags=["user management"])
class UserViewSet(viewsets.ModelViewSet):
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field = 'id'
  
  def get_queryset(self):
    return CustomUser.objects.all()
  
  @extend_schema(
    request=None,
    description="retrieve the list of organizations followed by currently authenticated user.",
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
    description="retrieve the list of events bookmarked by currently authenticated user.",
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
    
  @extend_schema(
    description="Partially update the authenticated user's profile. (normal user not organizer)",
    request=ProfileSerializer,
    responses=ProfileSerializer
  )
  @action(detail=False, methods=['patch'], url_path='profile')
  def update_my_profile(self, request):
    try:
      profile = request.user._user_profile
    except Profile.DoesNotExist:
        return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    
    serialized_user = self.serializer_class(request.user)

    return Response(serialized_user.data)
  
  @extend_schema(description="Retrieve a paginated list of ratings created by the currently authenticated user so far.")
  @action(detail=False, methods=['get'])
  def ratings(self, request):
    user = request.user
    ratings = Rating.objects.filter(user=user).order_by('-created_at')
    
    paginator = ResponsePagination()
    paginated = paginator.paginate_queryset(ratings, request)
    serialized = UserRatingSerializer(paginated, many=True, context={'request': request})
    
    return paginator.get_paginated_response(
      serialized.data
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