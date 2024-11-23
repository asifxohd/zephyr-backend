from django.urls import path, re_path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<id>\w+)/$', ChatConsumer.as_asgi()),
]