import logging
from rest_framework import serializers
from .models import Category, Event, Hashtag, Bookmark, Rating
from apps.community.models import Community
from apps.user.serializers import UserWithOrganizationProfileDocSerializer
from drf_spectacular.utils import extend_schema_field
from django.db.models import Avg
from apps.event.rating.serializers import RatingSerializer


logger = logging.getLogger("django")
class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = [
      'id',
      'organizer',
      'name',
      'description',
      'created_at',
      'updated_at',
    ]
    read_only_fields = ['id','organizer', 'created_at','updated_at']

  def create(self, validated_data):
    request = self.context.get('request')
    
    category = Category.objects.create(
      organizer=request.user,
      **validated_data
    )
    
    return category
    
class HashtagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Hashtag
    fields = ['name']

class EventSerializer(serializers.ModelSerializer):
  category = serializers.PrimaryKeyRelatedField(
    many=True,
    queryset=Category.objects.all()
  )
  organizer = UserWithOrganizationProfileDocSerializer(read_only=True)
  hashtags_list = serializers.ListField(
    child=serializers.CharField(),
    write_only=True,
    help_text="List of hashtag names"
  )
  cover_image_url = serializers.ListField(
      child=serializers.URLField(), 
      allow_empty=True,
      required=False,
      help_text="List of cover image URLs"
  )
  
  hashtags = HashtagSerializer(many=True, read_only=True)
  likes_count = serializers.SerializerMethodField(help_text="Number of likes (integer)")
  liked = serializers.SerializerMethodField(help_text="Whether the user liked the event (boolean)")
  bookmarks_count = serializers.SerializerMethodField(help_text="Number of bookmarks (integer)")
  bookmarked = serializers.SerializerMethodField(help_text="Whether the user bookmarked the event (boolean)")

  rated = serializers.SerializerMethodField(help_text="Weather the user rated the event (boolean)")
  rating_count = serializers.SerializerMethodField(help_text='Retrieve the count of ratings')
  average_rating = serializers.SerializerMethodField()
  rating = serializers.SerializerMethodField()
  
  
  class Meta:
    model = Event
    fields = [
      'id',
      'organizer',
      'category',
      'title',
      'description',
      'start_time',
      'end_time',
      'start_date',
      'end_date',
      'location',
      'latitude',
      'longitude',
      'cover_image_url',
      'is_public',
      'onsite_payement',
      'hashtags',
      'hashtags_list',
      'likes_count',
      'liked',
      'rated',
      'average_rating',
      'rating_count',
      'bookmarks_count',
      'rating',
      'bookmarked',
      'created_at',
      'updated_at',
    ]
    read_only_fields = ['id', 'organizer', 'created_at', 'updated_at']
    
  @extend_schema_field(serializers.IntegerField())
  def get_likes_count(self, obj):
    return obj.likes.all().count()
  
  @extend_schema_field(serializers.BooleanField())
  def get_liked(self, obj):
    request = self.context.get('request')
    return obj.is_liked(request.user)
  
  @extend_schema_field(serializers.IntegerField())
  def get_bookmarks_count(self, obj):
    return Bookmark.objects.filter(event=obj).count()  
  
  @extend_schema_field(serializers.BooleanField())
  def get_bookmarked(self, obj):
    request = self.context.get('request')
    return Bookmark.objects.filter(user=request.user, event=obj).exists()
  
  @extend_schema_field(serializers.BooleanField())
  def get_rated(self, obj):
    request = self.context.get('request')
    return Rating.objects.filter(user=request.user, event=obj).exists()
  
  @extend_schema_field(serializers.IntegerField())
  def get_rating_count(self, obj):
    return Rating.objects.filter(event=obj).count()
  
  @extend_schema_field(serializers.FloatField(allow_null=True))
  def get_average_rating(self, obj):
    result = Rating.objects.filter(event=obj).aggregate(avg_rating=Avg('value'))
    return result['avg_rating']
  
  @extend_schema_field(RatingSerializer)
  def get_rating(self, obj):
      request = self.context.get('request')
      try:
          rating = Rating.objects.get(event=obj, user=request.user)
          return RatingSerializer(rating, context=self.context).data
      except Rating.DoesNotExist:
          return None
        
  def validate_hashtags_list(self, value):
    if not all(isinstance(name, str) and name.strip() for name in value):
      raise serializers.ValidationError("Each hashtag must be a non-empty string.")
    return value

  def create(self, validated_data):
    request = self.context.get('request')
    category_objs = validated_data.pop('category', [])
    hashtag_names = validated_data.pop('hashtags_list', [])
    cover_image_urls = validated_data.pop('cover_image_url', [])
    
    event = Event.objects.create(
      organizer=request.user,
      **validated_data
    )
    
    event.category.set(category_objs)
    hashtags = []
    for name in hashtag_names:
      hashtag, _ = Hashtag.objects.get_or_create(name=name)
      hashtags.append(hashtag)
    event.hashtags.set(hashtags)
    
    event.cover_image_url = cover_image_urls
    event.save()

    Community.objects.create(
      event=event,
      name=event.title,
      description=event.description
    )
    logger.info(f"Community created for event '{event.title}' (ID: {event.id})")

    return event

  def update(self, instance, validated_data):
    category_objs = validated_data.pop('category', None)
    hashtag_names = validated_data.pop('hashtags_list', None)
    cover_image_urls = validated_data.pop('cover_image_url', None)

    for attr, value in validated_data.items():
      setattr(instance, attr, value)
    instance.save()

    if category_objs is not None:
      instance.category.set(category_objs)
      
    if hashtag_names is not None:
      hashtags = []
      for name in hashtag_names:
        hashtag, _ = Hashtag.objects.get_or_create(name=name)
        hashtags.append(hashtag)
      instance.hashtags.set(hashtags)
    
    if cover_image_urls is not None:
      instance.cover_image_url = cover_image_urls
      instance.save()

    return instance