from django.shortcuts import render
from lit_reviews.forms import S3DirectUploadForm
from lit_reviews.custom_permissions import protected_project

@protected_project
def search_dashboard(request, id):
    file_form = S3DirectUploadForm()
    context = {"file_form": file_form}
    
    return render(request, "lit_reviews/run_searches.html", context=context)

##########################################################
# Below code is no longer used we are
# using DRF now you can find related logic 
# for belows functionalities here lit_review.api.search_dashboard
##########################################################
