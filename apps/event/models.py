from django.db import models
from apps.user.models import CustomUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField

class Category(models.Model):
    organizer = models.ForeignKey(CustomUser, related_name='categories', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
      
class Hashtag(models.Model):
  name = models.CharField(max_length=20, unique=True)
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
  cover_image_url = ArrayField(
      models.URLField(),
      blank=True,
      default=list
  ) 
  is_public = models.BooleanField(default=True)
  onsite_payement = models.BooleanField(default=False)
  
  hashtags = models.ManyToManyField(Hashtag, related_name='events')
  likes = models.ManyToManyField(CustomUser,related_name='likes')
  
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
      return self.title
    
  def is_liked(self, user):
    """Check if the given user has liked this event."""
    if user.is_authenticated:
        return self.likes.filter(id=user.id).exists()
    return False
  
  def get_avg_rating(self):
    return self.ratings.aggregate(avg_rating=models.Avg('value'))['avg_rating']
  
class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    name = models.CharField(max_length=255)
    description = models.TextField(default=None, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.price} ETB"
      
class UserTicket(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,related_name="tickets", null=True, blank=True)
  ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="users_purchased")
  purchase_date = models.DateTimeField(auto_now_add=True)
  used = models.BooleanField(default=False)
  
  class Meta:
    ordering =['-purchase_date']
  
class Bookmark(models.Model):
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bookmarks')
  event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookmarks')
  created_at = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    ordering = ['-created_at']
    
class Rating(models.Model):
  event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ratings')
  user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings')
  value = models.FloatField(
      validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
      help_text="Rating must be between 0.0 and 5.0"
  )
  comment = models.TextField(blank=True,null=True, help_text="Optional comment about the event")
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  

  def __str__(self):
      return f"{self.event.title} - {self.value}/5"