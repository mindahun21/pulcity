from rest_framework import serializers
from .models import Category, Event
from apps.community.models import Community
from apps.user.serializers import UserWithOrganizationProfileDocSerializer

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
    
    

class EventSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Category.objects.all()
    )
    organizer = UserWithOrganizationProfileDocSerializer(read_only=True)
    #TODO: pay_onsite

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
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'organizer', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        category_objs = validated_data.pop('category', [])
        
        event = Event.objects.create(
            organizer=request.user,
            **validated_data
        )
        
        event.category.set(category_objs)

        Community.objects.create(
            event=event,
            name=event.title,
            description=event.description
        )

        return event

    def update(self, instance, validated_data):
        category_objs = validated_data.pop('category', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if category_objs is not None:
            instance.category.set(category_objs)

        return instance