from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import AddUserToCommunitySerializer, CommunitySerializer
from .models import UserCommunity, Community
from apps.user.models import CustomUser
from rest_framework.response import Response
from rest_framework import (
  permissions,
  status,
  serializers,
  viewsets,
)
from drf_spectacular.utils import extend_schema,OpenApiResponse,inline_serializer
from rest_framework.decorators import action
from commons.permisions import IsOrganization
from commons.utils import ResponsePagination

@extend_schema(tags=["Community management"])
class AddUserToCommunityApiView(APIView):
  serializer_class = AddUserToCommunitySerializer
  permission_classes = [permissions.IsAuthenticated]
  
  
  @extend_schema(
    description="Add user (specified by payload user_id) to community created for event (specified by payload event_id)",
    responses={
      200:OpenApiResponse(
        inline_serializer(
          name="LikeUnlikeResponse",
          fields={"detail":serializers.CharField(),}
        )
      ),
      400:OpenApiResponse(
        inline_serializer(
          name="ErrorResponse",
          fields={"detail":serializers.CharField(),}
        )
      )
    }
  )
  def post(self, request):
    serializer = self.serializer_class(request.data)
    if serializer.is_valid():
      user= CustomUser.objects.get(id=serializer.validated_data.get('user_id'))
      community = Community.objects.get(event__id=serializer.validated_data.get('event_id'))
      _, created = UserCommunity.objects.get_or_create(user=user, community=community)
      
      if not created:
        return Response({"detail":"user is already in the community"},status=status.HTTP_400_BAD_REQUEST)
      
      return Response({'detail':"user successfully added to the community"}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["Community management"])
class CommunityViewSet(viewsets.ModelViewSet):
  lookup_field ='id'
  serializer_class = CommunitySerializer
  
  def get_queryset(self):
    return Community.objects.all()
  
  def get_permissions(self):
    if self.action in []:
      return [permissions.IsAuthenticated(), IsOrganization()]
    return [permissions.IsAuthenticated()]
  
  def get_serializer_context(self):
    context = super().get_serializer_context()
    context['request'] = self.request
    return context
  
  @extend_schema(
    request=None,
    description="retrieve the list of communities authenticated user is in.",
    responses=CommunitySerializer(many=True)
  )
  @action(detail=False, methods=['get'],url_path='me/community')
  def my_community(self, request):
    user = request.user
    my_communities = UserCommunity.objects.filter(user=user).order_by('-joined_at')
    paginator = ResponsePagination()
    paginated_communities = paginator.paginate_queryset(my_communities, request)
    serialized_communities = CommunitySerializer([community.community for community in paginated_communities],context={'request':request}, many=True)

    return paginator.get_paginated_response(
      serialized_communities.data
    )
    
  @extend_schema(exclude=True)
  def list(self, request):
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def create(self, request):
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