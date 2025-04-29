from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.event.event.views import EventViewSet
from apps.event.category.views import CategoryViewSet
from apps.event.ticket.views import TicketViewSet

router = DefaultRouter()
router.register('events',EventViewSet, basename='event')
router.register('categories',CategoryViewSet, basename='category')
router.register('tickets',TicketViewSet,basename='ticket')

urlpatterns = [
    
]

urlpatterns += router.urls
