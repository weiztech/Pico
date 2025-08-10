from django.urls import path

from .views import AppSchemaView

urlpatterns = [
    path("schema/<str:app_id>", AppSchemaView.as_view(), name="schema"),
]
