from django.db import models
from django.contrib.auth.models import AbstractUser,Group, Permission
from django.core.validators import MinLengthValidator
from django.utils import timezone


class CustomUser(AbstractUser):
  USER_ROLES = (
    ('organization', 'Organization'),
    ('user', 'User'),
  )
  
  email = models.EmailField(unique=True)
  is_verified = models.BooleanField(default=False)
  role = models.CharField(max_length=20, choices=USER_ROLES, default='user')

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = ['username']
  
  @property
  def profile(self):
      if self.role == 'organization':
          return getattr(self, '_organization_profile', OrganizationProfile.objects.get_or_create(user=self)[0])
      return getattr(self, '_user_profile', Profile.objects.get_or_create(user=self)[0])

  def __str__(self):
      return self.email

  def follow(self, user):
    """Follow another user"""
    if not self.is_following(user):
      Follow.objects.get_or_create(follower=self, followed=user)

  def unfollow(self, user):
      """Unfollow another user"""
      Follow.objects.filter(follower=self, followed=user).delete()

  def is_following(self, user):
      """Check if the user is following another user"""
      return Follow.objects.filter(follower=self, followed=user).exists()

  def followers_count(self):
      """Return the number of followers"""
      return self.followers.count()

  def following_count(self):
      """Return the number of users this user is following"""
      return self.following.count()

  def __str__(self):
    return self.email
  

class Profile(models.Model):
  user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='_user_profile')
  bio = models.CharField(max_length=255, blank=True)
  
  profile_photo_url = models.CharField(max_length=255, blank=True,null=True)
  phone_number = models.CharField(max_length=20, blank=True, null=True)
  date_of_birth = models.DateField(blank=True, null=True)
  location = models.CharField(max_length=255, blank=True ,null=True)  
  interests = models.JSONField(blank=True, null=True) 

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

class OrganizationProfile(models.Model):
  VERIFICATION_STATUS = (
    ('approved', 'Approved'),
    ('pending', 'Pending'),
    ('denied', 'Denied'),
  )
  
  user = models.OneToOneField(
      CustomUser,
      on_delete=models.CASCADE,
      related_name='_organization_profile'
  )
  name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
  description = models.TextField(blank=True, null=True)
  logo_url = models.CharField(max_length=255, blank=True,null=True)
  contact_phone = models.CharField(max_length=20, blank=True, null=True)
  website_url = models.URLField(blank=True, null=True)
  social_media_links = models.JSONField(blank=True, null=True)
  verification_id = models.CharField(max_length=255, blank=True, null=True)
  verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
      return self.name
      
      
class Follow(models.Model):
    follower = models.ForeignKey(CustomUser, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(CustomUser, related_name='followers', on_delete=models.CASCADE)
    followed_role = models.CharField(max_length=20, choices=CustomUser.USER_ROLES)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f'{self.follower.email} follows {self.followed.email}'

class OTP(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE) 
    otp = models.CharField(max_length=6) 
    created_at = models.DateTimeField(auto_now_add=True)  
    is_verified = models.BooleanField(default=False)  

    @property
    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 300  # 5 minutes in seconds
    
    def __str__(self):
        return f"OTP for {self.user.email}"