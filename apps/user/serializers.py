from rest_framework import serializers
from .models import Profile, OrganizationProfile, CustomUser
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from rest_framework.exceptions import ValidationError 


class ProfileSerializer(serializers.ModelSerializer):
  first_name = serializers.CharField(required=False, write_only=True)
  last_name = serializers.CharField(required=False, write_only=True)
  class Meta:
      model = Profile
      fields = '__all__'
      read_only_fields = ['user', 'created_at', 'updated_at'] 
  
  def update(self, instance, validated_data):
    first_name = validated_data.pop('first_name', None)
    last_name = validated_data.pop('last_name', None)
    
    user= instance.user
    if first_name is not None:
      user.first_name = first_name
    
    if last_name is not None:
      user.last_name = last_name
    
    user.save()

    return super().update(instance, validated_data)


class OrganizationProfileSerializer(serializers.ModelSerializer):
    is_following = serializers.SerializerMethodField(read_only=True)
    
    social_media_links = serializers.JSONField(
        required=False, allow_null=True, help_text="A JSON object of social media links, e.g. {'twitter': '...', 'facebook': '...'}"
    )
    class Meta:
        model = OrganizationProfile
        fields = '__all__'
        extra_fields = ['is_following'] 
        read_only_fields = ['user', 'created_at', 'updated_at','verification_status'] 
        
    @extend_schema_field(serializers.BooleanField())
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

