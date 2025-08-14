from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from core.consumers import NotificationConsumer

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path("ws/notifications/", NotificationConsumer.as_asgi()),
    ]),
})