import uuid
import base64
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Chat


@receiver(pre_save, sender=Chat)
def generate_chat_id(sender, instance, **kwargs):
    if not instance.id and not instance.chat_id:
        # Generate a unique, URL-safe chat_id
        instance.chat_id = base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b'=').decode('ascii')