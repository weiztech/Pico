from django.core.exceptions import PermissionDenied
from functools import wraps
from lit_reviews.models import LiteratureReview
from accounts.models import Subscription

def protected_project(view):
    """
    Protected projects can not be accessed by all clients
    only clients that own the project or admins or non client users.
    """
    @wraps(view)
    def _view(request, *args, **kwargs):
        lit_id = kwargs.get("id")
        if lit_id:
            literature_review = LiteratureReview.objects.get(id=lit_id)
            if literature_review not in request.user.my_reviews():
                raise PermissionDenied
                
        return view(request, *args, **kwargs)
    return _view

def manager_required(view):
    @wraps(view)
    def _view(request, *args, **kwargs):
        # for company users all have full access
        # for citemed ops team only staff users have this permission
        if not request.user.is_staff and not request.user.client:
            raise PermissionDenied
                
        return view(request, *args, **kwargs)
    return _view

