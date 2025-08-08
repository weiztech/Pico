from django.contrib import admin
from .models import Chat, ChatMessage


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    """Admin configuration for Chat model."""

    list_display = ('id', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin configuration for ChatMessage model."""

    list_display = ('id', 'chat', 'user', 'created_at')
    list_filter = ('chat', 'user', 'created_at')
    search_fields = ('content',)
    readonly_fields = ('created_at',)
