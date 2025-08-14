from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from backend.logger import logger

class isClient(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_client


class isArticleOwner(BasePermission):

    def has_object_permission(self, request, view, obj):
        # client = request.user.client
        # ops_team_article = any([is_company_client for is_company_client in obj.reviews.values_list("search__literature_review__client__is_company", flat=True)])
        # if client:
        #     article_clients = obj.reviews.values_list("search__literature_review__client", flat=True)
        #     client_id = obj.literature_review.client.id if obj.literature_review.client else None
        #     article_owner = client.id in [*article_clients, client_id]
        #     return article_owner
        # elif request.user.is_ops_member and ops_team_article:
        #     return True
        # elif request.user.is_staff or request.user.is_superuser:
        #     return True 
        # else:
        #     return False
        
        if request.user.is_ops_member or request.user.is_client:
            for review in obj.reviews:
                if review in request.user.my_reviews():
                    return True
            return False
        
        elif request.user.is_staff or request.user.is_superuser:
            return True 
        
        else:
            return False

    