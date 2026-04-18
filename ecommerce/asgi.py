import os 
os.environ.setdefault("DJANGO_SETTINGS_MODULE","ecommerce.settings")


from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter,URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from chat.middleware import JWTAuthMiddleware
import chat.routing


application=ProtocolTypeRouter({
    "http":get_asgi_application(),  # normal Django handles HTTP
    "websocket":AllowedHostsOriginValidator(
        JWTAuthMiddleware(

            URLRouter(chat.routing.websocket_urlpatterns)
        )
    ),

})