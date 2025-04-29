from rest_framework import serializers
from .models import Category, Event

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
    category = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
    )

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
        category_ids = validated_data.pop('category', [])
        
        # Set organizer from request.user
        event = Event.objects.create(
            organizer=request.user,
            **validated_data
        )
        
        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            event.category.set(categories)

        return event

    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category', None)
        
        # Update all other fields normally
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if category_ids is not None:
            categories = Category.objects.filter(id__in=category_ids)
            instance.category.set(categories)

        return instance