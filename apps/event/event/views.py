from rest_framework import(
  viewsets,
  permissions,
  status,
  serializers
)
from rest_framework.response import Response
from apps.event.serializers import EventSerializer
from apps.event.rating.serializers import RatingSerializer
from apps.event.models import Event, Ticket, UserTicket, Bookmark, Rating, Category, Hashtag
from apps.event.ticket.serializers import TicketSerializer,UserTicketSerializer
from commons.permisions import IsOrganization
from commons.utils import ResponsePagination
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiParameter
from rest_framework.decorators import action, permission_classes

from django.db.models import Q, Avg, Count,FloatField, Value
from django.db.models.expressions import RawSQL
from django.utils import timezone
from functools import reduce
from operator import or_

import logging
logger = logging.getLogger('django')

@extend_schema(tags=["Event management"])
class EventViewSet(viewsets.ModelViewSet):
  serializer_class = EventSerializer
  lookup_field = 'id'
  
  def get_queryset(self):
    return Event.objects.all()
  
  def get_permissions(self):
    if self.action in ['update', 'delete', 'partial_update', 'create']:
      return [permissions.IsAuthenticated(), IsOrganization()]
    elif self.action in ['popular']:
      return [permissions.AllowAny()]
    return [permissions.IsAuthenticated()]
  
  @extend_schema(
    description="Retreve all tickets for Event specified by the parameter id.",
    responses=TicketSerializer(many=True)
  )
  @action(detail=True, methods=['get'])
  def tickets(self, request, id=None):
    event = self.get_object()
    tickets = Ticket.objects.filter(event=event)
    serializer = TicketSerializer(tickets,many=True)
    return Response({"tickets": serializer.data},status=status.HTTP_200_OK)
  
  @extend_schema(
    description="Retrieve all tickets a user bought for an event specified by the event ID. "
                "Optionally filter by whether the ticket was used (used=true/false).",
    parameters=[
        OpenApiParameter(
            name='used',
            type=bool,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Optional filter to get only used or unused tickets (true/false)."
        )
    ],
    responses=UserTicketSerializer(many=True)
  )
  @action(detail=True, methods=['get'], url_path='user/tickets')
  def user_tickets(self, request, id=None):
    event = self.get_object()
    user = request.user

    user_tickets = UserTicket.objects.filter(
        user=user,
        ticket__event=event
    )

    used_param = request.query_params.get('used')
    if used_param is not None:
        if used_param.lower() in ['true', '1']:
            user_tickets = user_tickets.filter(used=True)
        elif used_param.lower() in ['false', '0']:
            user_tickets = user_tickets.filter(used=False)

    paginator = ResponsePagination()
    paginated_user_tickets = paginator.paginate_queryset(user_tickets, request)

    serializer = UserTicketSerializer(paginated_user_tickets, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)

  @extend_schema(
    description="Toggle liked status of the event specified by the parameter id for authenticated user.",
    request=None,
    responses={
      200:OpenApiResponse(
        inline_serializer(
          name="LikeUnlikeResponse",
          fields={"detail":serializers.CharField(),}
        )
      ),
      400:OpenApiResponse(
        inline_serializer(
          name="ErrorResponse",
          fields={"detail":serializers.CharField(),}
        )
      )
    }
  )
  @action(detail=True,methods=['post'])
  def like(self, request, id=None):
    event = self.get_object()
    user = request.user
    if user == event.organizer:
      return Response({'detail':"can't like your event"},status=status.HTTP_400_BAD_REQUEST)
    
    if event.is_liked(request.user):
      event.likes.remove(user)
      return Response({'detail':"event unliked"},status=status.HTTP_200_OK)
    else:
      event.likes.add(user)
      return Response({'detail':"event Liked"},status=status.HTTP_200_OK)
    
  @extend_schema(
    description="Toggle bookmark status of the event specified by the parameter id for authenticated user.",
    request=None,
    responses={
      200:OpenApiResponse(
        inline_serializer(
          name="BookmarkResponse",
          fields={"detail":serializers.CharField(),}
        )
      ),
      201:OpenApiResponse(
        inline_serializer(
          name="BookmarkResponse",
          fields={"detail":serializers.CharField(),}
        )
      )
    }
  )
  @action(detail=True, methods=['post'])
  def bookmark(self, request, id=None):
    event = self.get_object()
    user = request.user
    
    bookmark = Bookmark.objects.filter(user=user, event=event).first()
    if bookmark:
      bookmark.delete()
      return Response({'detail': 'Bookmark removed'}, status=status.HTTP_200_OK)
    else:
      Bookmark.objects.create(user=user, event=event)
      return Response({'detail':'Bookmark added'}, status=status.HTTP_201_CREATED)

  @extend_schema(
    description=(
        "Search for events by matching keywords in the title, description, or location. "
        "Filter results by categories and hashtags (comma-separated). "
        "Results are ordered by average rating and number of likes."
    ),
    parameters=[
        OpenApiParameter(
            name='q',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Search keyword(s) to match against title, description, or location.'
        ),
        OpenApiParameter(
            name='category',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Comma-separated category names to filter events by category.'
        ),
        OpenApiParameter(
            name='hashtags',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Comma-separated hashtag names to filter events by hashtags.'
        ),
    ],
    responses={
        200: EventSerializer(many=True)
    }
  )
  @action(detail=False, methods=['get'], url_path='search')
  def search(self, request):
    query = request.query_params.get('q', '')
    hashtags_param = request.query_params.get('hashtags', '')
    category_param = request.query_params.get('category', '')

    words = query.strip().split()
    
    search_filters = reduce(or_, [
        Q(title__icontains=word) |
        Q(description__icontains=word) |
        Q(location__icontains=word)
        for word in words
    ]) if words else Q()

    events = Event.objects.filter(search_filters)

    if category_param:
        categories = [cat.strip() for cat in category_param.split(',')]
        events = events.filter(category__name__in=categories)
    if hashtags_param:
        hashtags = [tag.strip() for tag in hashtags_param.split(',')]
        events = events.filter(hashtags__name__in=hashtags)

    events = events.annotate(
        avg_rating=Avg('ratings__value'),
        likes_count=Count('likes')
    ).distinct().order_by('-avg_rating', '-likes_count')
    
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)

    serializer = self.get_serializer(paginated_events, many=True,context={"request":request})
    return paginator.get_paginated_response(  
      serializer.data
    )
      
  @extend_schema(
    description="Retrieve the most recent events, ordered by creation time.",
    responses={200: EventSerializer(many=True)}
  )
  @action(detail=False, methods=['get'], url_path='filter/recent')
  def recent(self, request):
    events = Event.objects.all().order_by('-created_at')
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)

    serializer = self.get_serializer(paginated_events, many=True,context={"request":request})
    return paginator.get_paginated_response(  
      serializer.data
    )
    
  @extend_schema(
    description="Retrieve the most popular events based on average rating and number of likes.",
    responses={200: EventSerializer(many=True)}
  )
  @action(detail=False, methods=['get'], url_path='filter/popular')
  def popular(self, request):
    events = (
        Event.objects.annotate(
            avg_rating=Avg('ratings__value'),
            likes_count=Count('likes')
        )
        .order_by('-avg_rating', '-likes_count')
      )
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)

    serializer = self.get_serializer(paginated_events, many=True,context={"request":request})
    return paginator.get_paginated_response(  
      serializer.data
    )
    
  @extend_schema(
    description="Retrieve recent events from organizers the user follows. "
                  "Events are ordered by creation date (most recent first).",
    responses={200: EventSerializer(many=True)}
  )
  @action(detail=False, methods=['get'], url_path='filter/following')
  def recent(self, request):
    user = request.user
    followed_organizer_ids = user.following.values_list('followed_id', flat=True)

    events = (
        Event.objects.filter(organizer__id__in=followed_organizer_ids)
        .order_by('-created_at')
    )
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)

    serializer = self.get_serializer(paginated_events, many=True,context={"request":request})
    return paginator.get_paginated_response(  
      serializer.data
    )
    
  @extend_schema(
      description="Filter events by geographic proximity using latitude, longitude, and radius in kilometers.",
      parameters=[
          OpenApiParameter(name='lat', type=float, location=OpenApiParameter.QUERY, required=True, description='User latitude'),
          OpenApiParameter(name='lng', type=float, location=OpenApiParameter.QUERY, required=True, description='User longitude'),
          OpenApiParameter(name='radius', type=float, location=OpenApiParameter.QUERY, required=True, description='Radius in kilometers'),
      ],
      responses={200: EventSerializer(many=True)}
  )
  @action(detail=False, methods=['get'], url_path='filter/nearby')
  def nearby(self, request):
      try:
          lat = float(request.query_params.get('lat'))
          lng = float(request.query_params.get('lng'))
          radius = float(request.query_params.get('radius'))
      except (TypeError, ValueError):
          return Response({'detail': 'lat, lng, and radius are required and must be floats.'}, status=400)

      haversine_sql = """
          6371 * acos(
              cos(radians(%s)) * cos(radians(latitude)) *
              cos(radians(longitude) - radians(%s)) +
              sin(radians(%s)) * sin(radians(latitude))
          )
      """

      events = Event.objects.annotate(
          distance=RawSQL(haversine_sql, (lat, lng, lat))
      ).filter(distance__lte=radius).order_by('distance')

      serializer = self.get_serializer(events, many=True, context={'request': request})
      return Response(serializer.data, status=200)
      
  @extend_schema(
    description="Retrieve upcoming events that the authenticated user has purchased tickets for.",
    responses={200: EventSerializer(many=True)}
  )
  @action(detail=False, methods=['get'])
  def upcoming(self, request):
    user = request.user
    current_time = timezone.now()

    user_tickets = UserTicket.objects.filter(user=user).select_related('ticket__event')
    events = Event.objects.filter(
        tickets__users_purchased__in=user_tickets,
        start_date__gte=current_time
    ).distinct().order_by('start_date')

    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)

    serializer = self.get_serializer(paginated_events, many=True,context={"request":request})
    return paginator.get_paginated_response(  
      serializer.data
    )
    
  @extend_schema(
    description="Retrieve paginated event ratings for event specified by id.",
    responses={200: RatingSerializer(many=True)}
  )
  @action(detail=True, methods=['get'])
  def ratings(self, request, id=None):
    event = self.get_object()
    ratings = Rating.objects.filter(event=event)
    
    paginator = ResponsePagination()
    paginated_ratings = paginator.paginate_queryset(ratings, request)

    serializer = RatingSerializer(paginated_ratings, many=True,context={"request":request})
    return paginator.get_paginated_response(  
      serializer.data
    ) 
    
  @extend_schema(
    request=None,
    description="retrieve the list of events attended by currently authenticated user.",
    responses=EventSerializer(many=True)
  )
  @action(detail=False, methods=['get'], url_path='attended')
  def attended(self, request):
    user = request.user
    user_tickets = UserTicket.objects.filter(user=user, used=True).select_related('ticket__event')

    event_ids = user_tickets.values_list('ticket__event_id', flat=True).distinct()
    events = Event.objects.filter(id__in=event_ids)

    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)
    serialized_events = EventSerializer(paginated_events, many=True, context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_events.data
    )
    
  @extend_schema(
    request=None,
    responses={
        200: EventSerializer(many=True),
    },
  )
  @action(detail=False, methods=['get'])
  def recomendations(self, request):
    """
    Retrieve a list of recommended events for the currently authenticated user.

    The recommendations are based on the user's saved interests and social behavior:
    
    - **Categories**: Events that belong to categories the user is interested in.
    - **Hashtags**: Events that contain tags matching the user's interests.
    - **Followed Organizers**: Events organized by users the current user follows.

    The result is sorted by highest average rating and most likes.

    **Authentication required.**
    """
    user = request.user
    interests = user.profile.interests or {}
    

    categories = interests.get('categories', [])
    tags = interests.get('tags', [])
    followed_orgs = user.following.values_list('followed', flat=True)
    logger.info(f"User {user.id} interests - Categories: {categories}, Tags: {tags}")

    category_objs = Category.objects.filter(name__in=categories)
    hashtag_objs = Hashtag.objects.filter(name__in=tags)

    logger.info(f"User {user.id} matching hashtags: {[h.name for h in hashtag_objs]}")

    events = Event.objects.filter(
      Q(category__in=category_objs) |
      Q(hashtags__in=hashtag_objs) |
      Q(organizer__in=followed_orgs)
    ).distinct() if category_objs or hashtag_objs or followed_orgs else Event.objects.all()

    events = events.annotate(
        avg_rating=Avg('ratings__value'),
        likes_count=Count('likes')
    ).order_by('-avg_rating', '-likes_count')
    
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)
    serialized_events = EventSerializer(paginated_events, many=True, context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_events.data
    )
    
  
  
  
  

    
      
      