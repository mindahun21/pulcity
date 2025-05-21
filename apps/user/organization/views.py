from django.utils import timezone
from django.db.models.functions import TruncMonth
from django.db.models import Count
from collections import OrderedDict

from datetime import timedelta
from django.db.models import Sum, F
from rest_framework import (
  viewsets,
  status,
  permissions,
  serializers
)
from rest_framework.response import Response
from rest_framework.decorators import action

from apps.event.models import Event, Category, UserTicket, Ticket
from apps.user.models import CustomUser, OrganizationProfile
from apps.payment.models import Payment , PaymentItem
from apps.community.models import Community

from apps.user.serializers import UserSerializer, OrganizationProfileSerializer
from apps.event.serializers import EventSerializer, CategorySerializer
from ..serializers import UserWithAnyProfileDocSerializer, UserWithOrganizationProfileDocSerializer
from .serializers import ScanSerializer
from apps.community.serializers import CommunitySerializer

from ..utils import ResponsePagination
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiParameter
from commons.permisions import IsOrganization


@extend_schema(tags=["Organization Management"])
class OrganizationViewSet(viewsets.ModelViewSet):
  serializer_class = UserSerializer
  lookup_field ='id'   
  
  def get_queryset(self):
    return CustomUser.objects.filter(role='organization')
  
  def get_permissions(self):
    if self.action in ['org_followers','events','analytics','groups']:
      return [permissions.IsAuthenticated(), IsOrganization()]
    elif self.action in ['scan','verify']:
      return [permissions.AllowAny()]
    return [permissions.IsAuthenticated()]
  
  @extend_schema(
    request=None, 
    responses={
        200: OpenApiResponse(
          inline_serializer(
              name="FollowingResponse",
              fields={"detail": serializers.CharField(),}
            ), 
          description="Successfully followed the organization"
          ),
        400: OpenApiResponse(inline_serializer(name="FollowingErrorResponse", fields={"detail": serializers.CharField()}), description="organization is already followed"),
    },
  )
  @action(detail=True, methods=['post'])
  def follow(self, request, id=None):
      user_to_follow = self.get_object()
      if request.user.is_following(user_to_follow):
        return Response({'detail':"Already followed!"},status=status.HTTP_400_BAD_REQUEST)
      request.user.follow(user_to_follow)
      return Response({"detail": "following"},status=status.HTTP_200_OK)

  @extend_schema(
      request=None, 
      responses={
          200: OpenApiResponse(
              inline_serializer(
                  name="UnfollowResponse",
                  fields={
                      "detail": serializers.CharField(),
                  },
              ),
              description="Successfully unfollowed the organization",
          ),
          400: OpenApiResponse(
              inline_serializer(
                  name="UnfollowErrorResponse",
                  fields={
                      "detail": serializers.CharField(),
                  },
              ),
              description="Organization is already not followed",
          ),
      },
  )
  @action(detail=True, methods=['post'])
  def unfollow(self, request, id=None):
      user_to_unfollow = self.get_object()
      if request.user.is_following(user_to_unfollow):
        request.user.unfollow(user_to_unfollow)
        return Response({"detail": "unfollowed"},status=status.HTTP_200_OK)
      
      return Response({"detail": "Already not followed"}, status=status.HTTP_400_BAD_REQUEST)
    
  @extend_schema(
      description="Paginated Followers for organization specified by id",
      request=None,
      responses={
          200: OpenApiResponse(
              inline_serializer(
                  name="PaginatedFollowersResponse",
                  fields={
                      "count": serializers.IntegerField(),
                      "next": serializers.URLField(allow_null=True),
                      "previous": serializers.URLField(allow_null=True),
                      "results": UserWithAnyProfileDocSerializer(many=True),
                  },
              ),
              description="A paginated list of followers",
          ),
      },
  )
  @action(detail=True,methods=['get'])
  def followers(self, request,id=None):
    paginator = ResponsePagination()
    org = self.get_object()
    followers = org.followers.all().order_by('-created_at')
    paginated_followers = paginator.paginate_queryset(followers, request)
    serialized_followers = UserSerializer([f.follower for f in paginated_followers], many=True,context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_followers.data
    )
    
  @extend_schema(
    description="Paginated Followers for currently authenticated organization",
    request=None,
    responses={
        200: OpenApiResponse(
            inline_serializer(
                name="PaginatedFollowersResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "next": serializers.URLField(allow_null=True),
                    "previous": serializers.URLField(allow_null=True),
                    "results": UserWithAnyProfileDocSerializer(many=True),
                },
            ),
            description="A paginated list of followers",
        ),
    },
  )
  @action(detail=False,methods=['get'], url_path='me/followers')
  def org_followers(self, request,id=None):
    paginator = ResponsePagination()
    org = request.user
    followers = org.followers.all().order_by('-created_at')
    paginated_followers = paginator.paginate_queryset(followers, request)
    serialized_followers = UserSerializer([f.follower for f in paginated_followers], many=True,context={'request': request})
    
    return paginator.get_paginated_response(
      serialized_followers.data
    )
    
  @extend_schema(
    description="Retrieve a paginated list of events organized by the currently authenticated organization.",
    responses=EventSerializer(many=True)
  )
  @action(detail=False,methods=['get'])
  def events(self, request):
    events = Event.objects.filter(organizer=self.request.user)
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)
    serialized_events = EventSerializer(paginated_events, many=True,context={'request':request})
    
    return paginator.get_paginated_response(  
      serialized_events.data
    )
    
  @extend_schema(
    description="Retrieve a paginated list of events organized by the organization specified by the parameter id.",
    responses=EventSerializer(many=True)
  )
  @action(detail=True, methods=['get'], url_path='events')
  def organizer_events(self, request, id=None):
    org = self.get_object()
    events = Event.objects.filter(organizer=org)
    
    paginator = ResponsePagination()
    paginated_events = paginator.paginate_queryset(events, request)
    serialized_events = EventSerializer(paginated_events, many=True, context={'request':request})
    
    return paginator.get_paginated_response(  
      serialized_events.data
    )
    
  @extend_schema(
    description="Retrieve a paginated list of categories organized by the organization specified by the parameter id.",
    responses=CategorySerializer(many=True)
  )
  @action(detail=True,methods=['get'])
  def categories(self, request, id=None):
    org = self.get_object()
    categories = Category.objects.filter(organizer=org)
    
    paginator = ResponsePagination()
    paginated_categories = paginator.paginate_queryset(categories, request)
    serialized_categories = CategorySerializer(paginated_categories, many=True)
    
    return paginator.get_paginated_response(  
      serialized_categories.data
    )
    
  @extend_schema(
      description="Retrieve dashboard overview analytics for currently authenticated organization",
      responses=OpenApiResponse(
          response=inline_serializer(
              name="DashboardAnalyticsResponse",
              fields={
                  "events": inline_serializer(
                      name="AnalyticsSummary",
                      fields={
                          "total": serializers.IntegerField(),
                          "percentage_change": serializers.FloatField()
                      }
                  ),
                  "users": inline_serializer(
                      name="UserAnalyticsSummary",
                      fields={
                          "total": serializers.IntegerField(),
                          "percentage_change": serializers.FloatField()
                      }
                  ),
                  "revenue": inline_serializer(
                      name="RevenueAnalyticsSummary",
                      fields={
                          "total": serializers.FloatField(),
                          "percentage_change": serializers.FloatField()
                      }
                  ),
                  "event_growth": serializers.DictField(
                      child=serializers.IntegerField(),
                      help_text="Events created per month over the last 12 months"
                  ),
                  "user_growth": serializers.DictField(
                      child=serializers.IntegerField(),
                      help_text="Users (ticket buyers) per month over the last 12 months"
                  )
              }
          )
      )
  )
  @action(detail=False, methods=['get'])
  def analytics(self, request):
    org = request.user
    return Response({
      "events":self._get_total_events_analytics(org),
      "users": self._get_total_user_analytics(org),
      "revenue":self._get_total_revenue_analytics(org),
      "event_growth":self._get_events_last_12_months(org),
      "user_growth":self._get_user_growth_last_12_months(org)
    }, status=status.HTTP_200_OK)
    
  @extend_schema(
    description="Scan user tickets on the event gates (making the ticket used)",
    request=ScanSerializer(),
    responses=OpenApiResponse(
          response=inline_serializer(
              name="AcanticketResponse",
              fields={
                      "detail": serializers.CharField(),
                      "user": serializers.CharField(),
                      "ticket": serializers.CharField(),
                      "event": serializers.CharField(),
                    }
                 
          )
      )
  )
  @action(detail=False,methods=['post'], url_path='tickets/scan')
  def scan(self, request):
    serializer = ScanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_ticket = serializer.validated_data['user_ticket']
    event = serializer.validated_data['event']

    user_ticket.used = True
    user_ticket.save()

    return Response({
        "detail": "Ticket scanned successfully.",
        "user": user_ticket.user.email if user_ticket.user else None,
        "ticket": user_ticket.ticket.name,
        "event": event.title
    }, status=status.HTTP_200_OK)
    
  @extend_schema(
    description="Retreive all the groups associated with an organizer  ",
    responses=CommunitySerializer(many=True)
  )
  @action(detail=False, methods=['get'])
  def groups(self, request):
    org = request.user
    communities = Community.objects.filter(event__organizer=org).distinct()
    
    paginator = ResponsePagination()
    paginated_communities = paginator.paginate_queryset(communities, request)
    serialized = CommunitySerializer(paginated_communities, many=True, context={'request':request})
    
    return paginator.get_paginated_response(  
      serialized.data
    )
  
  @extend_schema(
    description="Update Currently authenticated organization profile .",
    request=OrganizationProfileSerializer(),
    responses=OrganizationProfileSerializer()
  )
  @action(detail=False, methods=['patch'], url_path='profile')
  def update_my_profile(self, request):
      try:
          profile = request.user._organization_profile
      except OrganizationProfile.DoesNotExist:
          return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)

      serializer = OrganizationProfileSerializer(profile, data=request.data, partial=True)
      serializer.is_valid(raise_exception=True)
      serializer.save()
      return Response(serializer.data)

  @extend_schema(
      description="Change the verification_status of an organization.",
      request=None,
      parameters=[
          OpenApiParameter(
              name="status",
              description="New verification status (e.g., pending, approved, rejected)",
              required=True,
              type=str
          )
      ],
      responses=OrganizationProfileSerializer(),
      methods=["POST"],
      operation_id="verifyOrganizationStatus", 
  )
  @action(detail=True, methods=['post'], url_path='verify')
  def verify(self, request, id=None):
    status_param = request.query_params.get("status")
    allowed_statuses = ['pending', 'approved', 'denied']

    if not status_param:
        return Response(
            {"detail": "Missing required 'status' query parameter."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if status_param not in allowed_statuses:
        return Response(
            {"detail": f"Invalid status. Must be one of {allowed_statuses}."},
            status=status.HTTP_400_BAD_REQUEST
        )  
        
    org = self.get_object()
    try:
        profile = org._organization_profile
    except OrganizationProfile.DoesNotExist:
          return Response({'detail': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    profile.verification_status = status_param
    profile.save()
    serializer = OrganizationProfileSerializer(profile)
    return Response(serializer.data, status=status.HTTP_200_OK)
    
  @extend_schema(responses=UserWithOrganizationProfileDocSerializer())
  def retrieve(self, request, *args, **kwargs):
    return super().retrieve(request, *args, **kwargs)
    
  @extend_schema(exclude=True)
  def list(self, request):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
  
  @extend_schema(exclude=True)
  def create(self, request):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
      
  @extend_schema(exclude=True)
  def update(self, request, id=None):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def partial_update(self, request, id=None):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

  @extend_schema(exclude=True)
  def destroy(self, request, id=None):
      """Hidden from schema."""
      return Response({'detail': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
  def _get_month_date_ranges(self):
    now = timezone.now()
    this_month_start = now.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    
    return this_month_start, last_month_start, last_month_end
  
  def _calculate_percentage_change(self, old, new):
    if old == 0:
        return 100 if new > 0 else 0
    return round(((new - old) / old) * 100, 2)
  
  def _get_total_events_analytics(self, organizer):
    this_month_start, last_month_start, _ = self._get_month_date_ranges()
    recent_events = Event.objects.filter(
      organizer=organizer,
      created_at__gte = last_month_start
    )
    this_month_events_count = sum(1 for e in recent_events if e.created_at >= this_month_start)
    last_month_events_count = recent_events.count() - this_month_events_count
    
    percentage_change = self._calculate_percentage_change(last_month_events_count,this_month_events_count)
        
    total = Event.objects.filter(organizer=organizer).count()
        
    return {
      "total": total,
      "percentage_change": percentage_change
    }
    
  def _get_total_user_analytics(self, organizer):
    this_month_start, last_month_start, _ = self._get_month_date_ranges()

    total = UserTicket.objects.filter(ticket__event__organizer = organizer).count()
    recent_tickets = UserTicket.objects.filter(
      ticket__event__organizer=organizer,
      purchase_date__gte=last_month_start
    )
    this_month_user_tickets_count = sum(1 for t in recent_tickets if t.purchase_date >= this_month_start)
    last_month_user_tickets_count = recent_tickets.count() - this_month_user_tickets_count

    
    percentage_change = self._calculate_percentage_change(last_month_user_tickets_count, this_month_user_tickets_count)
    return {
      "total": total,
      "percentage_change": percentage_change
    }
    
  def _get_total_revenue_analytics(self, organizer):
    this_month_start, last_month_start, _ = self._get_month_date_ranges()
    ticket_ids = Ticket.objects.filter(event__organizer=organizer).values_list('id', flat=True)

    total = PaymentItem.objects.filter(
      ticket_id__in=ticket_ids,
      payment__status='success'
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
    
    this_month_total = PaymentItem.objects.filter(
        ticket_id__in=ticket_ids,
        payment__status='success',
        payment__created_at__gte=this_month_start,
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0

    last_month_total = PaymentItem.objects.filter(
        ticket_id__in=ticket_ids,
        payment__status='success',
        payment__created_at__gte=last_month_start,
        payment__created_at__lt=this_month_start,
    ).aggregate(total=Sum(F('unit_price') * F('quantity')))['total'] or 0
    
    percentage_change = self._calculate_percentage_change(last_month_total, this_month_total)
    
    return {
      "total": total,
      "percentage_change": percentage_change
    }

  def _get_events_last_12_months(self, organizer):
    today = timezone.now().date()
    start_date = today.replace(day=1) - timedelta(days=365)

    # Get monthly counts
    monthly_counts = (
        Event.objects.filter(organizer=organizer, created_at__gte=start_date)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    monthly_data = OrderedDict()
    for i in range(12):
        month_date = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_name = month_date.strftime('%b %Y')  # e.g., "Apr 2025"
        monthly_data[month_name] = 0

    for entry in monthly_counts:
        month_name = entry['month'].strftime('%b %Y')
        if month_name in monthly_data:
            monthly_data[month_name] = entry['count']

    return OrderedDict(reversed(list(monthly_data.items())))
    
  def _get_user_growth_last_12_months(self, organizer):
    today = timezone.now().date()
    start_date = today.replace(day=1) - timedelta(days=365)

    # Query: Group UserTickets by month
    monthly_counts = (
        UserTicket.objects.filter(
            ticket__event__organizer=organizer,
            purchase_date__gte=start_date
        )
        .annotate(month=TruncMonth('purchase_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    monthly_data = OrderedDict()
    for i in range(12):
        month_date = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_label = month_date.strftime('%b %Y')  
        monthly_data[month_label] = 0

    for entry in monthly_counts:
        label = entry['month'].strftime('%b %Y')
        if label in monthly_data:
            monthly_data[label] = entry['count']

    return OrderedDict(reversed(list(monthly_data.items())))