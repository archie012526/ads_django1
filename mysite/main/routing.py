# main/routing.py
from django.urls import re_path
from . import consumers
from django.urls import re_path
from .consumers import PopularJobsConsumer


websocket_urlpatterns = [
    re_path(r"ws/popular_jobs/$", consumers.PopularJobsConsumer.as_asgi()),
]
# main/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/popular_jobs/$", consumers.PopularJobsConsumer.as_asgi()),
]

websocket_urlpatterns = [
    re_path(r'ws/popular-jobs/$', PopularJobsConsumer.as_asgi()),
]