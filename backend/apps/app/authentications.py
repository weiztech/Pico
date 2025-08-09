from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension

from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.contrib.auth import get_user_model


User = get_user_model()


class AppTokenAuthentication(TokenAuthentication):
    """
    Custom authentication class that authenticates users based on App token.
    
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Bearer ".  For example:
    
        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """
    
    keyword = 'Bearer'

    def authenticate(self, request):
        credentials = super().authenticate(request)
        if credentials:
            request.access_app = credentials[1]
        return credentials

    def get_model(self):
        from apps.app.models import App
        return App

    def authenticate_credentials(self, key):
        model = self.get_model()

        try:
            app = model.objects.select_related('user', 'tier').get(token=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token.')

        if not app.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted.')

        app.last_used_at = timezone.now()
        app.save(update_fields=['last_used_at'])

        return app.user, app

    def authenticate_header(self, request):
        return self.keyword


class AppTokenAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'apps.app.authentications.AppTokenAuthentication'
    name = 'AppTokenAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'Token',
            'description': 'App Token authentication. Format: Bearer <your_app_token>'
        }

