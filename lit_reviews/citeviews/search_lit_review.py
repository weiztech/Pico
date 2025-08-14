from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render

from ..models import LiteratureReview
from ..pmc_api import clear_literature_review_data
from ..tasks import process_props_async
from lit_reviews.custom_permissions import protected_project


@protected_project
def run_search(request, id):
    if request.method == "POST":
        clear_literature_review_data(LiteratureReview.objects.get(id=id))

        # proposals = LiteratureReviewSearchProposal.objects.filter(literature_review__id=id)
        print("process proposals - calling task")
        process_props_async.delay(id)
        print("after delay call")

        return JsonResponse(
            {
                "go_to": reverse(
                    "literature_reviews:article_review_list", kwargs={"id": id}
                )
            }
        )
    
    else:
        return render(request, "lit_reviews/run_search.html")


@protected_project
def search_protocol(request, id):
    LiteratureReview.objects.get(id=id)

    return render(
        request,
        "lit_reviews/search_protocol.html",
        {"template_error": "No Project created for this lit review, please contact support to create one"},
    )


#######################################################################
########### BELOW IS NOT LONGER USER REPLACE by search_protocol ######
#####################################################################
