from django.shortcuts import render
from lit_reviews.custom_permissions import protected_project

@protected_project
def home(request, id):
    return render(request, "lit_reviews/extraction_fields.html")