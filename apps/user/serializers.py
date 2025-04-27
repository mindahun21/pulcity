from rest_framework import serializers
from .models import Profile, OrganizationProfile, CustomUser



class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class OrganizationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationProfile
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role','username', 'profile']
        
    def get_profile(self, obj):
      profile = obj.profile
      if profile is None:
          return None
      if obj.role == 'organization':
          return OrganizationProfileSerializer(profile).data
      return ProfileSerializer(profile).data
