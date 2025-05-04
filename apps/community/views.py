from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import AddUserToCommunitySerializer
from .models import UserCommunity, Community
from apps.user.models import CustomUser
from rest_framework.response import Response
from rest_framework import (
  permissions,
  status,
)

class AddUserToCommunityApiView(APIView):
  serializer_class = AddUserToCommunitySerializer
  permission_classes = [permissions.IsAuthenticated]
  
  def post(self, request):
    serializer = self.serializer_class(request.data)
    if serializer.is_valid():
      user= CustomUser.objects.get(id=serializer.validated_data.get('user_id'))
      community = Community.objects.get(event__id=serializer.validated_data.get('event_id'))
      _, created = UserCommunity.objects.get_or_create(user=user, community=community)
      
      if created:
        return Response({"detail":"user is already in the community"},status=status.HTTP_400_BAD_REQUEST)
      
      return Response({'detail':"user successfully added to the community"}, status=status.HTTP_200_OK)