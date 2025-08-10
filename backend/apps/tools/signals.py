from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.common.encryption import FernetEncryption

from .models import UserTool

fernet_encryption = FernetEncryption()


@receiver(pre_save, sender=UserTool)
def encrypt_secret_key(sender, instance, **kwargs):
    """Encrypt the secret_key before saving the UserTool instance."""
    if (not instance.pk and instance.secret_key) or (
        instance.pk
        and instance.secret_key
        and (
            old_secret_key := UserTool.objects.filter(pk=instance.pk).values_list(
                "secret_key", flat=True
            )[0]
        )
        and old_secret_key != instance.secret_key
    ):
        instance.secret_key = fernet_encryption.encrypt(instance.secret_key)
