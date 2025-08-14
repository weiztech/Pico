from django.contrib.auth.models import BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def _create_user(self, username, email, client, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, client=client, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, client=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        if client:
            extra_fields.setdefault("is_client", True)
            if extra_fields.get("is_client") is not True:
                raise ValueError("Clientuser must have is_client=True.")
        return self._create_user(username, email, client, password, **extra_fields)

    def create_superuser(
        self, username, email, client=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(username, email, client, password, **extra_fields)


class UserQuerySet(models.QuerySet):
    def admins(self):
        return self.filter(is_active=True, is_superuser=True, is_client=False)

    def clients(self):
        return self.filter(is_active=True, is_superuser=False, is_client=True)

    def users(self):
        return self.filter(is_active=True, is_superuser=False, is_client=False)
