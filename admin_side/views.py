from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

# Create your views here.
def home(request):
    if request.user.is_staff:
        return render(request, "admin_side/home.html") 
    else:
        raise PermissionDenied