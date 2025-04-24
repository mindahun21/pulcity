from django.urls import path, include

urlpatterns = [
    path('auth/', include('user.auth_urls'))
]
