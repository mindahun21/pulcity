from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.user.organization.views import OrganizationViewSet
from apps.user.user.views import UserViewSet

router = DefaultRouter()
router.register('organizations', OrganizationViewSet ,basename='organization')
router.register('users',UserViewSet,basename='user')

urlpatterns = [
    path('auth/', include('apps.user.auth.urls'))
]

urlpatterns += router.urls
