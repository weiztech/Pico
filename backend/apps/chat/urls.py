from django.urls import path
from .views import ChatListView, ChatMessageListView

app_name = 'chat'

urlpatterns = [
    path('', ChatListView.as_view(), name='chat-list'),
    path('<int:chat_id>/messages/', ChatMessageListView.as_view(), name='chat-message-list'),
]
