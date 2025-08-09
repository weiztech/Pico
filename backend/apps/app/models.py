from django.db import models
from django.conf import settings


class App(models.Model):
    app_id = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apps'
    )
    token = models.CharField(max_length=100, unique=True)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['app_id', 'user'], name='unique_app_id_per_user')
        ]