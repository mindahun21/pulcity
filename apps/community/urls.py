from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('communities',views.CommunityViewSet, basename='community')

urlpatterns = [
    path("community/users/<int:id>/",views.AddUserToCommunityApiView.as_view(),name="add-user-community")
]

urlpatterns += router.urls