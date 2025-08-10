from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .apis import TOOLS_APIS

router = DefaultRouter()

for view_set in TOOLS_APIS:
    router.register(f"{view_set.url_prefix}", view_set, basename=view_set.api_basename)

urlpatterns = [
    # Tools API
    path("", include(router.urls)),
]
