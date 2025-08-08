from rest_framework import serializers
from .models import Chat, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""

    class Meta:
        model = ChatMessage
        fields = ('id', 'user', 'text', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class ChatSerializer(serializers.ModelSerializer):
    """Serializer for chats."""

    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ('id', 'user', 'created_at', 'updated_at', 'messages')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'messages')
