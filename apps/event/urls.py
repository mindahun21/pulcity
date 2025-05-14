from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.event.event.views import EventViewSet
from apps.event.category.views import CategoryViewSet
from apps.event.ticket.views import TicketViewSet
from apps.event.rating.views import RatingViewSet
from rest_framework_nested.routers import NestedDefaultRouter

router = DefaultRouter()
router.register('events',EventViewSet, basename='event')
router.register('categories',CategoryViewSet, basename='category')
router.register('tickets',TicketViewSet,basename='ticket')

event_router = NestedDefaultRouter(router, r'events', lookup='event')
event_router.register(r'rating', RatingViewSet, basename='event-rating')

urlpatterns = [
  path('', include(event_router.urls)),
]

urlpatterns += router.urls
