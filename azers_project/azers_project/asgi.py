"""
ASGI config for azers_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

# Django settings must be configured before importing routing, whose consumers
# import Django models at module load time.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "azers_project.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Finish Django's app initialization before routing imports WebSocket consumers
# (which import models).
django_asgi_app = get_asgi_application()

import core.routing

# application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            core.routing.websocket_urlpatterns
        )
    ),
})
