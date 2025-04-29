from rest_framework import serializers
from ..models import CustomUser, Profile, OrganizationProfile
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from ..models import CustomUser, Profile, OrganizationProfile
from django.core.validators import MinLengthValidator



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        user.is_active = False
        Profile.objects.create(user=user)
        return user



class OrganizationRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    
    # Profile fields
    name = serializers.CharField(write_only=True, validators=[MinLengthValidator(2)])
    description = serializers.CharField(required=False, allow_blank=True, write_only=True)
    logo_url = serializers.CharField(required=False, allow_null=True, write_only=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True, write_only=True)
    website_url = serializers.URLField(required=False, allow_blank=True, write_only=True)
    social_media_links = serializers.JSONField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'email','password',
            'name', 'description', 'logo_url',
            'contact_phone', 'website_url', 'social_media_links'
        ]

    def create(self, validated_data):
        # Extract profile fields
        profile_data = {
            'name': validated_data.pop('name'),
            'description': validated_data.pop('description', ''),
            'logo_url': validated_data.pop('logo_url', None),
            'contact_phone': validated_data.pop('contact_phone', ''),
            'website_url': validated_data.pop('website_url', ''),
            'social_media_links': validated_data.pop('social_media_links', {}),
        }

        user = CustomUser.objects.create_user(
              email=validated_data['email'],
              username=validated_data['email'],
              password=validated_data['password'],
              role='organization', 
          )        
        user.is_active = False
        user.save()

        OrganizationProfile.objects.create(user=user, **profile_data)

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
class VerifyEmailSerializer(serializers.Serializer):
  email = serializers.EmailField()
  otp= serializers.CharField()

class ResendOtpSerializer(serializers.Serializer):
  email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def save(self):
        email = self.validated_data['email']
        user = CustomUser.objects.get(email=email)
        user.set_password(self.validated_data['new_password'])
        user.save()
