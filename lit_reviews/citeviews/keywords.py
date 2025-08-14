from django.shortcuts import render

from lit_reviews.custom_permissions import protected_project

@protected_project
def keyword(request, id):
    return render(request, "lit_reviews/keyword_vue.html", {"test":" test"})