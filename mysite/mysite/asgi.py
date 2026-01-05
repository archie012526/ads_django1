import os
from django.core.asgi import get_asgi_application

# Channels disabled - not using WebSockets
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# import main.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Simple ASGI application without WebSocket support
application = get_asgi_application()

# Original channels configuration (commented out):
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             main.routing.websocket_urlpatterns
#         )
#     ),
# })

