import re
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login

from backend.settings import LOGIN_REQUIRED_URLS_EXCEPTIONS, RESTRICTED_URLS


class RequireLoginMiddleware:
    """
    Middleware component that wraps the login_required decorator around
    matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and
    define LOGIN_REQUIRED_URLS and LOGIN_REQUIRED_URLS_EXCEPTIONS in your
    settings.py. For example:
    ------
    LOGIN_REQUIRED_URLS = (
        r'/topsecret/(.*)$',
    )
    LOGIN_REQUIRED_URLS_EXCEPTIONS = (
        r'/topsecret/login(.*)$',
        r'/topsecret/logout(.*)$',
    )
    ------
    LOGIN_REQUIRED_URLS is where you define URL patterns; each pattern must
    be a valid regex.

    LOGIN_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly
    define any exceptions (like login and logout URLs).
    """

    def __init__(self, get_response):

        self.allowed = [re.compile(url) for url in LOGIN_REQUIRED_URLS_EXCEPTIONS]
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # No need to process URLs if user already logged in
        if request.user.is_authenticated or any(
            [pattern.match(request.path) for pattern in self.allowed]
        ):
            return None
        return login_required(view_func)(request, *view_args, **view_kwargs)

        # An exception match should immediately return None
        # for url in self.exceptions:
        #     if url.match(request.path):
        #         return None

        # Requests matching a restricted URL pattern are returned
        # wrapped with the login_required decorator
        # for url in self.required:
        #     if url.match(request.path):
        #         return login_required(view_func)(request, *view_args, **view_kwargs)

        # Explicitly return None for all non-matching requests
        # return None

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response


class RequirePermissionMiddleware(object):
    """
    Middleware component that wraps the permission_check decorator around
    views for matching URL patterns. To use, add the class to
    MIDDLEWARE_CLASSES and define RESTRICTED_URLS and
    RESTRICTED_URLS_EXCEPTIONS in your settings.py.

    For example:

    RESTRICTED_URLS = (
                          (r'/topsecet/(.*)$', 'auth.access_topsecet'),
                      )
    RESTRICTED_URLS_EXCEPTIONS = (
                          r'/topsecet/login(.*)$',
                          r'/topsecet/logout(.*)$',
                      )

    RESTRICTED_URLS is where you define URL patterns and their associated
    required permissions. Each URL pattern must be a valid regex.

    RESTRICTED_URLS_EXCEPTIONS is, conversely, where you explicitly define
    any exceptions (like login and logout URLs).
    """

    def __init__(self, get_response):

        self.restricted = [re.compile(url) for url in RESTRICTED_URLS]
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Requests matching a restricted URL pattern are returned
        # wrapped with the permission_required decorator
        if request.user.is_authenticated:
            if request.user.is_client and any(
                [pattern.match(request.path) for pattern in self.restricted]
            ):
                return redirect_to_login(next=request.path)
        return None

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
