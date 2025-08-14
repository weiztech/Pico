# views.py
from django.shortcuts import redirect


def redirect_view(request):
    # if request.user.is_client:
    #     return redirect("/client_portal/")
    # elif request.user.is_superuser:
    #     return redirect("/literature_reviews/")
    # else:
    #     return redirect("/literature_reviews/")

    return redirect("/literature_reviews/")
