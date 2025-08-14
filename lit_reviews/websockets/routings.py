# chat/routing.py
from django.urls import re_path

from lit_reviews.websockets import consumers

websocket_urlpatterns = [
    # re_path(r"ws/literature_review/(?P<room_name>\w+)/$", consumers.LiteratureReviewConsumer.as_asgi()),
    # path("ws/literature_review/<str:room_name>/", consumers.LiteratureReviewConsumer.as_asgi()),
    re_path(r"^ws/literature_review/(?P<room_name>[^/]+)/$", consumers.LiteratureReviewConsumer.as_asgi()),
    re_path(r"^ws/user/(?P<room_name>[^/]+)/$", consumers.UserConsumer.as_asgi()),
]