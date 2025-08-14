import threading

from accounts.models import User 

_user = threading.local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user
        response = self.get_response(request)

        # Clear cache after request is processed
        self.clear_user_cache()

        return response

    @staticmethod
    def get_current_user():
        return getattr(_user, 'value', None)
    
    @staticmethod
    def clear_user_cache():
        """Clear the user cache"""
        # Import here to avoid circular imports
        from lit_reviews.helpers.user import _request_cache
        if hasattr(_request_cache, 'current_user'):
            delattr(_request_cache, 'current_user')


# middleware.py

from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

class SubscriptionCheckMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Don't block staff, admin, or anonymous users
        if not request.user.is_authenticated:
            return None
        
        # Allow access to the subscription or logout page to avoid redirect loops
        allowed_paths = [
            reverse('accounts:logout'),
            reverse('accounts:subscription_required'),            
        ]
        if request.path in allowed_paths:
            return None

        try:
            licence = request.user.licence
            if not licence or not licence.is_valid:
                return redirect(reverse('accounts:subscription_required')) 
        except User.licence.RelatedObjectDoesNotExist:
            return redirect(reverse('accounts:subscription_required')) 
        
        return None
