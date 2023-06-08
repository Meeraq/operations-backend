from django.urls import re_path,path

from . import consumers

websocket_urlpatterns = [
    path('ws/meeting/', consumers.MeetingConsumer.as_asgi()),
]
