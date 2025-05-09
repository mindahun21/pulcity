from rest_framework import serializers
from .models import Profile, OrganizationProfile, CustomUser



class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class OrganizationProfileSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationProfile
        fields = '__all__'
        extra_fields = ['is_following'] 
        
    def get_is_following(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if user and user.is_authenticated:
            return user.is_following(obj.user)
        return False

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role','first_name','last_name','is_active','date_joined','username', 'profile']
        
    def get_profile(self, obj):
      profile = obj.profile
      if profile is None:
          return None
      if obj.role == 'organization':
          return OrganizationProfileSerializer(profile, context=self.context).data
      return ProfileSerializer(profile).data


class UserWithOrganizationProfileDocSerializer(serializers.ModelSerializer):
    profile = OrganizationProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role', 'first_name', 'last_name', 'is_active', 'date_joined', 'username', 'profile']



class UserWithAnyProfileDocSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role', 'first_name', 'last_name', 'is_active', 'date_joined', 'username', 'profile']

