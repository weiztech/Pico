from django.urls import path, include

from .views import (
    client_home,
    documents_library,
    project_details,
    projects_list,
    templates,
    vigilance,
    intake_form,
    actions,
    company_overview,
    event,
    report_overview,
    action_details,
    event_details,
    recall_details,
    article_details,
    automated_search,
    create_automated_search,
    automated_search_results,
    automated_search_update,
    export_automated_search_results,
)


app_name = "client_portal"
urlpatterns = [
    path("", client_home, name="client_home"),
    path("documents_library/", documents_library, name="documents_library"),
    path("project_details/<int:id>/", project_details, name="project_details"),
    path("projects_list/", projects_list, name="projects_list"),
    path("templates/", templates, name="templates"),
    path("vigilance/", vigilance, name="vigilance"),
    path("<int:id>/intake_form/", intake_form, name="intake_form"),
    path("actions/", actions, name="actions"),
    path("action_details/<int:id>", action_details, name="action_details"),
    path("company_overview/", company_overview, name="company_overview"),
    path("event/", event, name="event"),
    path("report_overview/", report_overview, name="report_overview"),
    path("events/<int:id>/details/", event_details, name="event_details"),
    path("recalls/<int:id>/details/", recall_details, name="recall_details"),
    path("articles/<int:id>/details/", article_details, name="article_details"),
    path("automated_search/", automated_search, name="automated_search"),
    path("create_automated_search/", create_automated_search, name="create_automated_search"),
    path("automated_search/<int:id>/", automated_search_update, name="automated_search_update"),
    path("automated_search_results/<int:id>/", automated_search_results, name="automated_search_results"),
    path("export_automated_search_results/<int:id>/", export_automated_search_results, name="export_automated_search_results"),
    

    path("api/", include("client_portal.api.urls")),
]
