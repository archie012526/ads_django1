# main/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/popular_jobs/$", consumers.PopularJobsConsumer.as_asgi()),
]
# main/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/popular_jobs/$", consumers.PopularJobsConsumer.as_asgi()),
]
