from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ToolCategoryListView,
    ToolListView,
    ToolDetailView,
    UserToolListView,
    UserToolDetailView,
    user_tool_stats
)
from .apis import TOOLS_APIS


router = DefaultRouter()

for view_set in TOOLS_APIS:
    router.register(
        f'{view_set.url_prefix}',
        view_set,
        basename=view_set.api_basename
    )

urlpatterns = [
    # Tool categories
    path('categories/', ToolCategoryListView.as_view(), name='categories'),

    # Tools
    path('', ToolListView.as_view(), name='tools'),
    path('<int:pk>/', ToolDetailView.as_view(), name='tool-detail'),
    
    # User tools
    path('user/', UserToolListView.as_view(), name='user-tools'),
    path('user/<int:pk>/', UserToolDetailView.as_view(), name='user-tool-detail'),
    path('user/stats/', user_tool_stats, name='user-tool-stats'),

    # Google Maps API
    path('', include(router.urls)),
]
