from rest_framework.permissions import BasePermission
from backend import settings

class isStaffUser(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff
    
class isClient(BasePermission):

    def has_permission(self, request, view):
        return request.user.client
    
class isNotClient(BasePermission):

    def has_permission(self, request, view):
        return not request.user.client

class doesClientHaveAccess(BasePermission):
    message = 'You must be the owner of this object.'
    def has_object_permission(self, request, view, obj):
        return obj.literature_review in request.user.my_reviews()
        
class doesClientHaveAccessToProposal(BasePermission):
    message = 'You must be the owner of this object.'
    
    def has_object_permission(self, request, view, obj):        
        return obj.literature_review in request.user.my_reviews()
    
class doesClientHaveAccessToReport(BasePermission):
    message = 'You must be the owner of this object.'
    def has_object_permission(self, request, view, obj):
        return obj.literature_review in request.user.my_reviews()


class isProjectOwner(BasePermission):
    """ 
    Does this user have permission to access this project ?
    """
    
    def has_permission(self, request, view):
        from lit_reviews.models import LiteratureReview
        lit_review_id = view.kwargs.get("id", None)
        if lit_review_id:
            literature_review = LiteratureReview.objects.get(id=lit_review_id)
            return literature_review in request.user.my_reviews()

        return True


class IsNotArchived(BasePermission):
    """
    Permission to check if the LiteratureReview related to the object is not archived.
    """
    message = "This literature review is archived and cannot be modified."

    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        # Only check for POST or other non-GET methods
        from lit_reviews.models import LiteratureReview
        lit_review_id = view.kwargs.get("id", None)
        if lit_review_id:
            try:
                literature_review = LiteratureReview.objects.get(id=lit_review_id)
                if literature_review.is_archived:
                    return False
            except LiteratureReview.DoesNotExist:
                # Optionally handle the case where the LiteratureReview does not exist
                return False
        return True
    

class DoesUserHaveEnoughCredits(BasePermission):
    """
    Permission to check if enough credits are left for those with credit based subscription.
    """
    message = f"""
    You've consumed all of your credits, 
    if you wish to include/exclude more articles you have to purchase more credits, 
    you can do so by following the link {settings.CREDITS_PURCHASE_LINK}
    """
    
    def has_permission(self, request, view):
        if request.method == "GET" or "state" not in request.data:
            return True

        # Only check for POST or other non-GET methods
        from accounts.models import Subscription
        user_licence = Subscription.objects.filter(user=request.user).first()
        is_credit_license = user_licence and user_licence.licence_type == "credits"
        if is_credit_license:
            if user_licence.remaining_credits > 0:
                return True 
            else:
                return False
        
        return True
    

class DoesUserHaveEnoughCreditsObjectPermission(BasePermission):
    """
    Permission to check if enough credits are left for those with credit based subscription.
    """
    message = f"""
    You've consumed all of your credits, 
    if you wish to include/exclude more articles you have to purchase more credits, 
    you can do so by following the link {settings.CREDITS_PURCHASE_LINK}
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method == "GET" or "state" not in request.data or obj.state not in ["U", "D"]:
            return True

        # Only check for POST or other non-GET methods
        from accounts.models import Subscription
        user_licence = Subscription.objects.filter(user=request.user).first()
        is_credit_license = user_licence and user_licence.licence_type == "credits"
        if is_credit_license:
            if user_licence.remaining_credits > 0:
                return True 
            else:
                return False
        
        return True
    

class DoesUserHaveEnoughCreditsForImportingArticles(BasePermission):
    """
    Permission to check if enough credits are left for those with credit based subscription.
    """
    message = f"""
    You have no credits left, if you wish to import more articles you have to purchase more credits, 
    you can do so by following the link {settings.CREDITS_PURCHASE_LINK}
    """
    
    def has_permission(self, request, view):
        if request.method == "GET":
            return True

        # Only check for POST or other non-GET methods
        from lit_reviews.models import LiteratureReview, ArticleReview
        from accounts.models import Subscription

        lit_review_id = view.kwargs.get("id", None)
        if lit_review_id:
            try:
                literature_review = LiteratureReview.objects.get(id=lit_review_id)
                reviews = ArticleReview.objects.filter(search__literature_review=literature_review)
                user_licence = Subscription.objects.filter(user=request.user).first()
                is_credit_license = user_licence and user_licence.licence_type == "credits"
                if is_credit_license and reviews.count() > (user_licence.plan_credits*2):
                    return False 
                else:
                    return True
                    
            except LiteratureReview.DoesNotExist:
                # Optionally handle the case where the LiteratureReview does not exist
                return False
        return False
    

class IsLivingReviewOwner(BasePermission):
    """ 
    Does this user have permission to access this project ?
    """
    
    def has_permission(self, request, view):
        from lit_reviews.models import LivingReview 

        lit_review_id = view.kwargs.get("id", None)
        if lit_review_id:
            living_review = LivingReview.objects.get(id=lit_review_id)
            return living_review.does_user_have_access(request.user)

        return True