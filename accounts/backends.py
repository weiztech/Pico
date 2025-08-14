from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from .models import User


class UserAuthBackend(ModelBackend):
    """Custom Auth User backend.
    User can log in with username or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user
