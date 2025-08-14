from lit_reviews.custom_permissions import protected_project
from django.shortcuts import render, get_object_or_404


@protected_project
def documents_library_view(request):
    state = request.GET.get("state")
    return render(request, "lit_reviews/documents_library.html", context={"state": state})