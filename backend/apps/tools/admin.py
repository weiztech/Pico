from django.contrib import admin
from .models import Tool, UserTool, ToolCategory


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ToolCategory model."""
    
    list_display = ('name', 'tool_count', 'color', 'order', 'created_at')
    list_editable = ('order',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('order', 'name')


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    """Admin configuration for Tool model."""
    
    list_display = ('name', 'category', 'version', 'is_active', 'user_count', 'created_at')
    list_filter = ('category', 'is_active', 'requires_authentication', 'requires_host', 'requires_api_key')
    search_fields = ('name', 'description', 'category')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'version', 'icon')
        }),
        ('Configuration', {
            'fields': ('is_active', 'requires_authentication', 'requires_host', 'requires_api_key', 'display')
        }),
        ('Documentation', {
            'fields': ('documentation_url',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserTool)
class UserToolAdmin(admin.ModelAdmin):
    """Admin configuration for UserTool model."""
    
    list_display = ('user', 'tool', 'display_name', 'is_active', 'usage_count', 'last_used')
    list_filter = ('is_active', 'tool__category', 'created_at')
    search_fields = ('user__email', 'tool__name', 'display_name', 'host_name')
    readonly_fields = ('created_at', 'updated_at', 'usage_count', 'last_used')
    raw_id_fields = ('user', 'tool')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'tool', 'display_name', 'is_active')
        }),
        ('Connection Settings', {
            'fields': ('host_name', 'port', 'secret_key'),
            'classes': ('collapse',)
        }),
        ('Advanced Configuration', {
            'fields': ('extra_config',),
            'classes': ('collapse',)
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tool')
