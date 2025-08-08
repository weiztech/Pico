from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Tool, ToolCategory, UserTool
from .serializers import (
    ToolCategorySerializer,
    ToolSerializer,
    UserToolCreateSerializer,
    UserToolDetailSerializer,
    UserToolUpdateSerializer,
)


@extend_schema(description='List all tool categories', tags=['Tools'])
class ToolCategoryListView(generics.ListAPIView):
    """List all tool categories."""

    queryset = ToolCategory.objects.active()
    serializer_class = ToolCategorySerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    description='List all available tools',
    tags=['Tools'],
    parameters=[
        OpenApiParameter(name='category', description='Filter by category', type=str),
        OpenApiParameter(name='search', description='Search for a tool', type=str),
    ],
)
class ToolListView(generics.ListAPIView):
    """List all available tools for user use."""

    queryset = Tool.objects.active()
    serializer_class = ToolSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')

        if category:
            queryset = queryset.filter(category=category)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(category__icontains=search)
            )

        return queryset


@extend_schema(description='Get tool details', tags=['Tools'])
class ToolDetailView(generics.RetrieveAPIView):
    """Get tool details."""

    queryset = Tool.objects.active()
    serializer_class = ToolSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(
    description='List user\'s tools or create a new user tool', tags=['User Tools']
)
class UserToolListView(generics.ListCreateAPIView):
    """List user's tools or create a new user tool."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTool.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserToolCreateSerializer
        return UserToolDetailSerializer


@extend_schema(
    description='Get, update, or delete a user tool',
    tags=['User Tools']
)
class UserToolDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a user tool."""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTool.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserToolUpdateSerializer
        return UserToolDetailSerializer


@extend_schema(
    description='Get user\'s tool usage statistics', tags=['User Tools']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tool_stats(request):
    """Get user's tool usage statistics."""
    user_tools = UserTool.objects.filter(user=request.request.user)

    stats = {
        'total_tools': user_tools.count(),
        'active_tools': user_tools.filter(is_active=True).count(),
        'total_usage': sum(tool.usage_count for tool in user_tools),
        'most_used_tool': None,
        'recent_tools': [],
    }

    # Most used tool
    most_used = user_tools.order_by('-usage_count').first()
    if most_used:
        stats['most_used_tool'] = {
            'name': most_used.tool.name,
            'usage_count': most_used.usage_count,
        }

    # Recently used tools
    recent = user_tools.filter(last_used__isnull=False).order_by('-last_used')[:5]
    stats['recent_tools'] = [
        {
            'name': tool.tool.name,
            'last_used': tool.last_used,
            'usage_count': tool.usage_count,
        }
        for tool in recent
    ]

    return Response(stats)
