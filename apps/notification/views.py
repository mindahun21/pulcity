from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework import(
  viewsets,
  permissions,
  status,
  serializers,
)
from .models import Notification
from commons.permisions import IsOrganization
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework.decorators import action

@extend_schema(tags=["Notification Management"])
class NotificationViewSet(viewsets.ModelViewSet):
  serializer_class = NotificationSerializer
  lookup_field = 'id'
  
  def get_queryset(self):
    return Notification.objects.all()
  
  def get_permissions(self):
    if self.action in ['list','read']:
      return [permissions.IsAuthenticated()]
    return [permissions.IsAuthenticated(), IsOrganization()]
  
  def list(self, request):
    user = request.user
    notifications = user.notifications.filter(read=False)
    serializer = self.serializer_class(notifications, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
  
  @extend_schema(
    description="set the read property of notification to True for the authenticated user",
    request=None,
    responses={
      200:OpenApiResponse(
        inline_serializer(name="ReadSuccessResponse",fields={"detail":serializers.CharField(),})
      ),
      400:OpenApiResponse(
        inline_serializer(name="ReadErrorResponse",fields={"detail":serializers.CharField(),})
      )
    }
  )
  @action(detail=True, methods=['post'])
  def read(self, request, id=None):
    notification = self.get_object()
    if notification.user == request.user:
      notification.read = True
      notification.save()
      return Response({"detail":"read operation success "}, status=status.HTTP_200_OK)
    else:
      return Response({"detail":" this notiication is not yours!"}, status=status.HTTP_400_BAD_REQUEST)      
  
  
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
