from rest_framework import (
  viewsets,
  status,
  permissions,
  serializers
)
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.user.serializers import UserSerializer
from apps.user.models import CustomUser
from ..utils import ResponsePagination
from apps.event.models import Event, Category
from apps.event.serializers import EventSerializer, CategorySerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from ..serializers import UserWithAnyProfileDocSerializer
from commons.permisions import IsOrganization


@extend_schema(tags=["Organization Management"])
class OrganizationViewSet(viewsets.ModelViewSet):
  serializer_class = UserSerializer
  permission_classes = [permissions.IsAuthenticated]
  lookup_field ='id'   
  
  def get_queryset(self):
    return CustomUser.objects.filter(role='organization')
  
  def get_permissions(self):
    if self.action in ['org_followers']:
      return [permissions.IsAuthenticated(), IsOrganization()]
    return [permissions.IsAuthenticated()]
  
  @extend_schema(
    request=None, 
    responses={
        200: OpenApiResponse(
          inline_serializer(
              name="FollowingResponse",
              fields={"detail": serializers.CharField(),}
            ), 
          description="Successfully followed the organization"
          ),
        400: OpenApiResponse(inline_serializer(name="FollowingErrorResponse", fields={"detail": serializers.CharField()}), description="organization is already followed"),
    },
  )
  @action(detail=True, methods=['post'])
  def follow(self, request, id=None):
      user_to_follow = self.get_object()
      if request.user.is_following(user_to_follow):
        return Response({'detail':"Already followed!"},status=status.HTTP_400_BAD_REQUEST)
      request.user.follow(user_to_follow)
      return Response({"detail": "following"},status=status.HTTP_200_OK)


  @extend_schema(
      request=None, 
      responses={
          200: OpenApiResponse(
              inline_serializer(
                  name="UnfollowResponse",
                  fields={
                      "detail": serializers.CharField(),
                  },
              ),
              description="Successfully unfollowed the organization",
          ),
          400: OpenApiResponse(
              inline_serializer(
                  name="UnfollowErrorResponse",
                  fields={
                      "detail": serializers.CharField(),
                  },
              ),
              description="Organization is already not followed",
          ),
      },
  )
  @action(detail=True, methods=['post'])
  def unfollow(self, request, id=None):
      user_to_unfollow = self.get_object()
      if request.user.is_following(user_to_unfollow):
        request.user.unfollow(user_to_unfollow)
        return Response({"detail": "unfollowed"},status=status.HTTP_200_OK)
      
      return Response({"detail": "Already not followed"}, status=status.HTTP_400_BAD_REQUEST)
    
  @extend_schema(
      description="Paginated Followers for organization specified by id",
      request=None,
      responses={
          200: OpenApiResponse(
              inline_serializer(
                  name="PaginatedFollowersResponse",
                  fields={
                      "count": serializers.IntegerField(),
                      "next": serializers.URLField(allow_null=True),
                      "previous": serializers.URLField(allow_null=True),
                      "results": UserWithAnyProfileDocSerializer(many=True),
                  },
              ),
              description="A paginated list of followers",
          ),
      },
  )
  @action(detail=True,methods=['get'])
  def followers(self, request,id=None):
    paginator = ResponsePagination()
    org = self.get_object()
    followers = org.followers.all().order_by('-created_at')
    paginated_followers = paginator.paginate_queryset(followers, request)
    serialized_followers = UserSerializer([f.follower for f in paginated_followers], many=True,context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_followers.data
    )
    
  @extend_schema(
    description="Paginated Followers for currently authenticated organization",
    request=None,
    responses={
        200: OpenApiResponse(
            inline_serializer(
                name="PaginatedFollowersResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "next": serializers.URLField(allow_null=True),
                    "previous": serializers.URLField(allow_null=True),
                    "results": UserWithAnyProfileDocSerializer(many=True),
                },
            ),
            description="A paginated list of followers",
        ),
    },
  )
  @action(detail=False,methods=['get'], url_path='me/followers')
  def org_followers(self, request,id=None):
    paginator = ResponsePagination()
    org = request.user
    followers = org.followers.all().order_by('-created_at')
    paginated_followers = paginator.paginate_queryset(followers, request)
    serialized_followers = UserSerializer([f.follower for f in paginated_followers], many=True,context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_followers.data
    )
    
  @extend_schema(
    description="Retrieve a paginated list of events organized by the currently authenticated organization.",
    responses=EventSerializer(many=True)
  )
  @action(detail=False,methods=['get'])
  def events(self, request):
    events = Event.objects.filter(organizer=self.request.user)
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)
    serialized_events = EventSerializer(paginated_events, many=True,context={'request':request})
    
    return paginator.get_paginated_response(  
      serialized_events.data
    )
    
  @extend_schema(
    description="Retrieve a paginated list of events organized by the organization specified by the parameter id.",
    responses=EventSerializer(many=True)
  )
  @action(detail=True, methods=['get'], url_path='events')
  def organizer_events(self, request, id=None):
    org = self.get_object()
    events = Event.objects.filter(organizer=org)
    
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)
    serialized_events = EventSerializer(paginated_events, many=True, context={'request':request})
    
    return paginator.get_paginated_response(  
      serialized_events.data
    )
    
  @extend_schema(
    description="Retrieve a paginated list of categories organized by the organization specified by the parameter id.",
    responses=CategorySerializer(many=True)
  )
  @action(detail=True,methods=['get'])
  def categories(self, request, id=None):
    org = self.get_object()
    categories = Category.objects.filter(organizer=org)
    
    paginator = ResponsePagination()
    paginated_categories = paginator.paginate_queryset(categories, request)
    serialized_categories = CategorySerializer(paginated_categories, many=True)
    
    return paginator.get_paginated_response(  
      serialized_categories.data
    )
    
  @extend_schema(exclude=True)
  def list(self, request):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
  
  @extend_schema(exclude=True)
  def create(self, request):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


  @extend_schema(exclude=True)
  def update(self, request, id=None):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def partial_update(self, request, id=None):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def destroy(self, request, id=None):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)