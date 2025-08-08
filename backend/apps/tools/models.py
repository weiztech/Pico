from django.db import models
from django.conf import settings

from .querysets import ToolCategoryQuerySet, ToolQuerySet


class Tool(models.Model):
    """Model representing available tools in the system."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        "tools.ToolCategory",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    version = models.CharField(max_length=20, default='1.0.0')
    
    # Tool configuration
    is_active = models.BooleanField(default=True)
    requires_authentication = models.BooleanField(default=False)
    requires_host = models.BooleanField(default=False)
    requires_api_key = models.BooleanField(default=False)
    display = models.BooleanField(default=False)
    
    # Metadata
    documentation_url = models.URLField(blank=True)
    icon = models.ImageField(upload_to='tool_icons/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ToolQuerySet.as_manager()
    
    class Meta:
        db_table = 'tools_tool'
        verbose_name = 'Tool'
        verbose_name_plural = 'Tools'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def user_count(self):
        """Return the number of users using this tool."""
        return self.user_tools.filter(is_active=True).count()


class UserTool(models.Model):
    """Model representing user's configured tools with their specific settings."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_tools'
    )
    tool = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name='user_tools'
    )
    
    # User-specific configuration
    display_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Connection settings
    host_name = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    secret_key = models.CharField(max_length=500, blank=True)
    
    # Additional configuration (JSON field for flexibility)
    extra_config = models.JSONField(default=dict, blank=True)
    
    # Usage tracking
    last_used = models.DateTimeField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tools_user_tool'
        verbose_name = 'User Tool'
        verbose_name_plural = 'User Tools'
        unique_together = ['user', 'tool']
        ordering = ['-last_used', 'tool__name']
    
    def __str__(self):
        return f"{self.user.email} - {self.display_name or self.tool.name}"
    
    @property
    def connection_string(self):
        """Generate a connection string if host and port are provided."""
        if self.host_name:
            if self.port:
                return f"{self.host_name}:{self.port}"
            return self.host_name
        return None
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        from django.utils import timezone
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])


class ToolCategory(models.Model):
    """Model for organizing tools into categories."""
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Icon class or name
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    order = models.PositiveIntegerField(default=0)
    display = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ToolCategoryQuerySet.as_manager()
    
    class Meta:
        db_table = 'tools_tool_category'
        verbose_name = 'Tool Category'
        verbose_name_plural = 'Tool Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def tool_count(self):
        """Return the number of tools in this category."""
        return self.tool_set.all().count()
