from rest_framework import(
  viewsets,
  permissions,
  status,
  serializers
)
from rest_framework.response import Response
from apps.event.serializers import EventSerializer
from apps.event.models import Event, Ticket, UserTicket, Bookmark
from apps.event.ticket.serializers import TicketSerializer
from commons.permisions import IsOrganization
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework.decorators import action


@extend_schema(tags=["Event management"])
class EventViewSet(viewsets.ModelViewSet):
  serializer_class = EventSerializer
  lookup_field = 'id'
  
  def get_queryset(self):
    return Event.objects.all()
  
  def get_permissions(self):
    if self.action in ['list', 'retrieve', 'user_tickets', 'tickets', 'like','bookmark']:
        return [permissions.IsAuthenticated()]
    return [permissions.IsAuthenticated(), IsOrganization()]
  
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
    description="Retreve all tickets a user bought for an event specified by the parameter id.",
    responses=TicketSerializer(many=True)
  )
  @action(detail=True, methods=['get'], url_path='user/tickets')
  def user_tickets(self, request, id=None):
    event = self.get_object()
    user = request.user

    user_tickets = UserTicket.objects.filter(
      user=user,
      ticket__event=event
    ).select_related('ticket')
    tickets = [ut.ticket for ut in user_tickets]
    serializer = TicketSerializer(tickets, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
  
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

