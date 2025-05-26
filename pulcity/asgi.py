import os
import django
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulcity.settings')
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.notification.middleware import JWTAuthMiddleware
from apps.notification.routing import websocket_urlpatterns 


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})

