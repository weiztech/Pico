import os
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render

from lit_reviews.models import *
from lit_reviews.forms import *

from django.http import HttpResponse
from lit_reviews.tasks import new_test_project
from lit_reviews.custom_permissions import protected_project, manager_required


@protected_project
def literature_reviews_home(request):    
    return render(request,"lit_reviews/literature_review_list_vue.html")

@protected_project
def literature_reviews_settings(request):    
    return render(request,"lit_reviews/literature_reviews_settings.html")

def citemed_ms_word_extention(request):   
    response = render(request,"lit_reviews/citemed_ms_word_extention.html")
    response["X-Frame-Options"] = "ALLOW-FROM https://*.sharepoint.com"
    response["Content-Security-Policy"] = "frame-ancestors https://*.office.com https://*.sharepoint.com"

    return response

@protected_project
def literature_review_detail(request, id):
    _fitler = Q(Q(id=id))
    review = LiteratureReview.objects.filter(_fitler).first()
    if review:
        return render(
            request,
            "lit_reviews/literature_review_detail.html",
            {
                "object": review,
                "article_url": reverse(
                    "lit_reviews:article_reviews_list", kwargs=dict(id=id)
                ),
                "search_protocol_url": reverse(
                    "lit_reviews:search_protocol", kwargs=dict(id=id)
                ),
            },
        )
    else:
        return render(request, "404.html") 

@protected_project
@manager_required
def archive_lit_review(request, id):
    lit_review_id = id
    review = LiteratureReview.objects.filter(id=lit_review_id).first()
    # is_allowed_client = request.user in review.authorized_users.all()
    # not_client = not request.user.is_client
    # if not_client or is_allowed_client:
    if review.is_archived :
        review.is_archived = False 
    else:
        review.is_archived = True 
    review.save()
    
    return HttpResponseRedirect(
        reverse("lit_reviews:literature_review_detail", args=[str(lit_review_id)])
    )

def create_test_project(request):
    if request.method == "POST":
        ltreview_id = request.POST.get("literature_review_id")
        device_name = request.POST.get("device_name")
        new_test_project.delay(projectid_to_copy=ltreview_id, device_name=device_name)
        return HttpResponse("OK")

def living_reviews(request):
    return render(request, "lit_reviews/living_reviews.html") 

def create_living_review(request):
    return render(request, "lit_reviews/create_living_review.html") 

def living_review_detail(request, id):
    return render(request, "lit_reviews/living_review_detail.html")