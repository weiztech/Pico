from lit_reviews.models import LiteratureReview
from client_portal.models import Project
from backend import settings
import os

ENV = os.getenv("ENV")

def literature_review_id(request):
    CELERY_DEFAULT_QUEUE = os.getenv("CELERY_DEFAULT_QUEUE", "")
    APP_VERSION = os.getenv("APP_VERSION", "")
    RELEASE_NOTES_LINK = os.getenv("RELEASE_NOTES_LINK", "")
    SHOW_AI_BETA = False 

    if "static/" in request.path or not request.resolver_match:
        return {}
    
    # Get the count of literature reviews for the current user
    # if request.user.is_authenticated and request.user.client and not request.user.is_superuser:
    #     literature_reviews_count = LiteratureReview.objects.filter(client=request.user.client).count()
    # elif request.user.is_authenticated and not request.user.client:
    #     literature_reviews_count = LiteratureReview.objects.filter(client__is_company=False).count()
    # else:
    #     literature_reviews_count = LiteratureReview.objects.all()
    if request.user.is_authenticated:
        literature_reviews_count = request.user.my_reviews().count()
        SHOW_AI_BETA = ( CELERY_DEFAULT_QUEUE != "PUBLIC" or request.user.is_superuser or request.user.is_ops_member )
        
    else:
        literature_reviews_count = 0

    # get literature review id from url
    lit_review_id = request.resolver_match.kwargs.get("id", "Unknown")
    project_type = None
    lit_review = None
    lit_review_title = None
    max_terms = None
    max_hits = None
    max_results = None
    project_details = {}
    is_archived = None

    project_name = None
    if lit_review_id != 'Unknown':
        request.session['literature_review_id'] = lit_review_id
        lit_review = LiteratureReview.objects.filter(id=lit_review_id).first()
        if lit_review and type(lit_review) == LiteratureReview:
            is_archived = lit_review.is_archived
            lit_review_title = lit_review.__str__()
            project_details["device_name"] = lit_review.device.name if lit_review.device else ""
            project_details["client_name"] = lit_review.client.name 
            project = Project.objects.filter(lit_review=lit_review).first()

            if project:
                project_details["project_name"] = project.project_name 
                project_type = project.get_type_display()
                project_name = project.project_name
                if CELERY_DEFAULT_QUEUE == "MAIN_PROD":
                    max_terms = project.max_terms
                    max_hits = project.max_hits
                    max_results = project.max_results

            else:
                project_details["project_name"] = "Not Found" 
                project_type = "Not Found"
                project_name = "Not Found"
                max_terms = None
                max_hits = None
                max_results = None
                

        else:
            lit_review_title = None

    context = {
        'literature_review_id': lit_review_id if lit_review_id else "Unknown",
        'lit_review': lit_review,
        'review_title': lit_review_title,
        'is_archived': is_archived,
        'env': ENV,
        'app_version': APP_VERSION,
        'realease_notes_link':RELEASE_NOTES_LINK,
        'project_type': project_type,
        'project_name': project_name,
        'max_terms': max_terms,
        'max_hits': max_hits,
        'max_results': max_results,
        "env_section": CELERY_DEFAULT_QUEUE,
        "project_details": project_details,
        "literature_reviews_count":literature_reviews_count,
        "support_email": settings.DEFAULT_FROM_EMAIL,
        "credits_purchase_link": settings.CREDITS_PURCHASE_LINK,
        "SHOW_AI_BETA": SHOW_AI_BETA,
    }
    return context
