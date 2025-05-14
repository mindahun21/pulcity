from rest_framework import (
  viewsets,
  permissions,
  exceptions,
  status,
)
from apps.event.models import Event, Rating
from commons.utils import ResponsePagination
from .serializers import RatingSerializer
from rest_framework.response import Response # full update: partial=False
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.decorators import action


@extend_schema(tags=["Rating management"])
class RatingViewSet(viewsets.ModelViewSet):
  permission_classes = [permissions.IsAuthenticated]
  serializer_class = RatingSerializer
  lookup_field = 'id'
  
  def get_event(self):
    try:
      return Event.objects.get(id=self.kwargs['event_id'])
    except Event.DoesNotExist:
        raise exceptions.NotFound("Event not found.")
  
  def get_rating(self):
      event = self.get_event()
      try:
          return Rating.objects.get(event=event, user=self.request.user)
      except Rating.DoesNotExist:
          raise exceptions.NotFound("Rating not found.")
        
  def get_queryset(self):
    return self.get_rating()
    

  def list(self, request, event_id=None):
    """Retrieve a paginated list of event ratings that have a comment. Only ratings with a non-empty comment are included."""
    event = self.get_event()
    ratings = Rating.objects.filter(event=event).exclude(comment__isnull=True).exclude(comment__exact='').order_by('-created_at')
    paginator = ResponsePagination()
    paginated_ratings = paginator.paginate_queryset(ratings, request)
    serialized_ratings = RatingSerializer(paginated_ratings, many=True, context={'request':request})
    
    return paginator.get_paginated_response(
      serialized_ratings.data
    )

  def create(self, request, event_id=None):
    """Create a new rating or overwrite an existing rating for the event. The user can rate the event for the first time or update their previous rating. no event id required to pass because only one rating exists per user for event """
    event = self.get_event()
    existing = Rating.objects.filter(event=event, user=request.user).first()

    if existing:
        serializer = RatingSerializer(existing, data=request.data, partial=True)
    else:
        serializer = RatingSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user, event=event)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
  
  @action(detail=False, methods=['get', 'patch', 'delete', 'put'], url_path='me')
  def me(self, request, event_id=None):
      """
      GET: Retrieve the logged-in user's rating for the event  \n
      PATCH: Update value/comment of the rating  \n
      DELETE: Delete the user's rating for the evet\n
      PUT: Fully update the rating (all required fields must be present)  
      """
      rating = self.get_rating()

      if request.method == 'GET':
          serializer = self.get_serializer(rating, context={'request': request})
          return Response(serializer.data, status=status.HTTP_200_OK)

      elif request.method == 'PATCH':
          serializer = self.get_serializer(rating, data=request.data, partial=True)
          serializer.is_valid(raise_exception=True)
          serializer.save()
          return Response(serializer.data, status=status.HTTP_200_OK)
      
      elif request.method == 'PUT':
        serializer = self.get_serializer(rating, data=request.data) 
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

      elif request.method == 'DELETE':
          rating.delete()
          return Response(status=status.HTTP_204_NO_CONTENT)

      return Response({"detail": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
  
  @extend_schema(exclude=True)
  def retrieve(self,request, *args, **kwargs):
      raise MethodNotAllowed("DELETE")
    
  @extend_schema(exclude=True)
  def update(self, *args, **kwargs):
      raise MethodNotAllowed("PUT")

  @extend_schema(exclude=True)
  def partial_update(self, *args, **kwargs):
      raise MethodNotAllowed("PATCH")

  @extend_schema(exclude=True)
  def destroy(self, *args, **kwargs):
      raise MethodNotAllowed("DELETE")


