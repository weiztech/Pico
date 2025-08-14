from django.urls import path, include
from .views import home

urlpatterns = [
    path("", home, name="admin-side-home"),
    path(
        "api/",
        include("admin_side.api.urls"),
    ),
] 