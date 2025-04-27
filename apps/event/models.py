from django.db import models
from apps.user.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator



class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Event(models.Model):
  organizer  = models.ForeignKey(CustomUser,related_name='events',on_delete=models.CASCADE)
  category = models.ManyToManyField(Category, related_name="events")
  title = models.CharField(max_length=255)
  description = models.TextField()
  start_time = models.DateTimeField()
  end_time = models.DateTimeField()
  start_date = models.DateTimeField()
  end_date = models.DateTimeField()
  location = models.CharField(max_length=255)
  latitude = models.FloatField(
          blank=True, null=True,
          validators=[
              MinValueValidator(-90),
              MaxValueValidator(90)
          ]
      )
  longitude = models.FloatField(
      blank=True, null=True,
      validators=[
          MinValueValidator(-180),
          MaxValueValidator(180)
      ]
  )
  cover_image_url = models.URLField(blank=True, null=True)
  is_public = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
      return self.title