from django.http import JsonResponse
from lit_reviews.models import *
from django.views.decorators.csrf import csrf_exempt
from lit_reviews.custom_permissions import protected_project



