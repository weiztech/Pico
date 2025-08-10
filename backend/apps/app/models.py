from functools import cached_property
from uuid import uuid4
from base64 import urlsafe_b64encode

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse

from apps.tools.functions import get_tool_choices, get_tool_prefix_map


class RequestAccessTier(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # RPS (Request Per Second)
    rps = models.IntegerField(default=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class App(models.Model):
    app_id = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apps'
    )
    token = models.CharField(max_length=100, unique=True)
    tier = models.ForeignKey("access_app.RequestAccessTier", on_delete=models.CASCADE, null=True, blank=True)
    schema_title = models.CharField(max_length=100, blank=True, help_text="Title of the API Schema.")
    schema_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Description for API Schema."
    )
    schema_description = models.TextField(blank=True)
    tools = ArrayField(
        models.CharField(max_length=50, choices=get_tool_choices()),
        default=list,
        blank=True,
        help_text="Select the tools to be use for the app."
    )

    # Timestamps
    last_used_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.app_id

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['app_id', 'user'], name='unique_app_id_per_user')
        ]

    @cached_property
    def list_tools_url_prefix(self):
        tools_map = get_tool_prefix_map()
        return { url_prefix for tool in self.tools if (url_prefix:= tools_map[tool]) }

    def get_schema_url(self):
        from os.path import join

        return join(
            settings.HOST,
            reverse('schema', kwargs={'app_id': self.app_id})[1:]
        )

    def allow_tool_by_url_prefix(self, url_prefix):
        list_tools_url_prefix = self.list_tools_url_prefix
        return url_prefix in list_tools_url_prefix

    def is_request_rate_limit(self):
        from .rate_limits import allow_request

        return allow_request(
            self.app_id,
            self.tier.rps,
        )

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.token:
                self.token = str(uuid4().hex)

            if not self.app_id:
                self.app_id = urlsafe_b64encode(
                    uuid4().bytes
                ).rstrip(b'=').replace(b"_", b"").decode('ascii')

        super().save(*args, **kwargs)
