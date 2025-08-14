from lit_reviews.models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from django.http import HttpResponse, JsonResponse
import json
import lit_reviews.tasks as task
from lit_reviews.forms import FinalReportConfigForm 
from client_portal.models import Project

# from lit_reviews.pmc_api import (
#     PubmedAPI,
#     materialize_search_proposal,
#     clear_literature_review_data,
#     get_count,
# )
from lit_reviews.tasks import *
from lit_reviews.custom_permissions import protected_project

@protected_project
def report_builder(request, id):
    if "type" in request.GET:
        report_type = request.GET["type"]
    else:
        report_type = "report"
    context = {
        "report_type": report_type,
    }

    return render(request, "lit_reviews/report_builder_vue.html",context)

##########################################################
# Below code is no longer used we are
# using DRF now you can find related logic 
# for belows functionalities here lit_review.api.report_builder
##########################################################