from django.db import models
from django.conf import settings


class Chat(models.Model):
    """Model representing a chat session."""
    chat_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chats'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_session'
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat with {self.user.email} at {self.created_at}"


class ChatMessage(models.Model):
    """Model representing a message within a chat."""
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    # only support text for now
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message'
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.email} in chat {self.chat.id}"
