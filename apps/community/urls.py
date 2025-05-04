from django.urls import path, include
from . import views

urlpatterns = [
    path("users/<int:id>/",views.AddUserToCommunityApiView.as_view(),name="add-user-community")
]
