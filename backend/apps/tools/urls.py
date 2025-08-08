
from django.urls import path
from .views import (
    ToolCategoryListView,
    ToolListView,
    ToolDetailView,
    UserToolListView,
    UserToolDetailView,
    user_tool_stats
)

app_name = 'tools'

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
]
