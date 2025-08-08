from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Chat, ChatMessage
from .serializers import ChatSerializer, ChatMessageSerializer


class ChatListView(generics.ListCreateAPIView):
    """List all chats or create a new chat."""

    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatMessageListView(generics.ListCreateAPIView):
    """List all messages for a chat or create a new message."""

    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatMessage.objects.filter(chat_id=self.kwargs['chat_id'])

    def perform_create(self, serializer):
        chat = Chat.objects.get(id=self.kwargs['chat_id'])
        serializer.save(chat=chat, sender=self.request.user)
