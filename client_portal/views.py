from django.shortcuts import render
from .models import (
    Project, 
    Action, 
    AutomatedSearchProject
)
from lit_reviews.models import (
    LiteratureReview,
    AdverseEventReview,
    AdverseRecallReview,
    Article,
    ArticleReview,
    Device,
)

from django.db.models import Q

def client_home(request):
    actions = []
    vigilance_data = []
    projects = Project.objects.filter(client=request.user.client)
    for project in projects:
        actions += Action.objects.filter(project=project)
    return render(
        request,
        "client_portal/client_home.html",
        {
            "actions": actions[:4],
            "vigilance_data": vigilance_data[:4],
            "projects": projects[:4],
        },
    )


def documents_library(request):
    # handeled by vue js now using json response to get data instead
    return render(request, "client_portal/documents_library.html")


def project_details(request, *args, **kwargs):
    project_id = kwargs.get("id")
    project = Project.objects.filter(id=project_id, client=request.user.client).first()
    return render(
        request,
        "client_portal/project_details.html",
        {"project": project},
    )


def projects_list(request):
    __filters = {"client": request.user.client}
    type_filter = request.GET.get("type_filter", "")
    if type_filter:
        __filters["type"] = type_filter

    projects = Project.objects.filter(**__filters)
    return render(
        request,
        "client_portal/projects_list.html",
        {"projects": projects},
    )


def templates(request):
    return render(request,template_name="client_portal/templates.html")


def vigilance(request):
    projects = Project.objects.filter(client=request.user.client, type="Vigilance")
    lit_reviews = [project.lit_review for project in projects]
    selected_status_str = request.GET.get("filter_status", None)
    selected_device_str = request.GET.get("filter_device", None)
    search_term = request.GET.get("search_term", "")
    __filters = {"search__literature_review__in": lit_reviews}

    if selected_status_str:
        selected_status = selected_status_str.split(",")
        __filters["state__in"] = selected_status
    else:
        selected_status = []

    if selected_device_str:
        selected_device = selected_device_str.split(",")
        selected_device = [int(item) for item in selected_device]
        __filters["search__literature_review__device__id__in"] = selected_device
    else:
        selected_device = []
    
    
    ae_events = AdverseEventReview.objects.filter(**__filters)
    if search_term:
        ae_events = ae_events.filter(
            Q(ae__description__icontains=search_term)
        )
    ae_recalls = AdverseRecallReview.objects.filter(**__filters)
    if search_term:
        ae_recalls = ae_recalls.filter(
            Q(ae__product_description__icontains=search_term)
        )
    articles = ArticleReview.objects.filter(**__filters)
    if search_term:
        articles = articles.filter(
            Q(article__title__icontains=search_term)
        )
    status_filter_choices = [*AdverseEventReview.FeedbackChoices.choices, *ArticleReview.ArticleReviewState.choices]
    device_filter_choices = Device.objects.all().order_by("name")

    return render(
        request,
        "client_portal/vigilance.html",
        {
            "ae_events": ae_events,
            "ae_recalls": ae_recalls,
            "articles": articles,
            "status_filter_choices": status_filter_choices,
            "device_filter_choices": device_filter_choices,
            "selected_status": selected_status,
            "selected_device": selected_device,
            "search_term":search_term
        }
    )


def intake_form(request, *args, **kwargs):
    project_id = kwargs.get("id")
    project = Project.objects.filter(id=project_id, client=request.user.client).first()
    return render(request, "client_portal/intake_form.html", {"project": project})


def actions(request):
    actions = []
    projects = Project.objects.filter(client=request.user.client)
    for project in projects:
        actions += Action.objects.filter(project=project)
    return render(
        request,
        "client_portal/actions.html",
        {"actions": actions},
    )


def action_details(request, *args, **kwargs):
    action_id = kwargs.get("id")
    action = Action.objects.filter(
        id=action_id, project__client=request.user.client
    ).first()
    if action:
        action.resolved_status = "read"
        action.save()
    return render(
        request,
        "client_portal/action_details.html",
        {"action": action},
    )


def company_overview(request):
    return render(request,template_name="client_portal/company_overview.html")


def event(request):
    return render(request,template_name="client_portal/event.html")


def report_overview(request):
    return render(request,template_name="client_portal/report_overview.html")

def event_details(request, id):
    state_choices = AdverseEventReview.FeedbackChoices.choices 
    if request.method == "POST":
        event = AdverseEventReview.objects.filter(id=id).first()
        state = request.POST.get("state")
        event.state = state
        event.save()

    event = AdverseEventReview.objects.filter(id=id).first()
    context = {"event": event, "state_choices": state_choices}
    return render(request, "client_portal/event_details.html", context)

def recall_details(request, id):
    state_choices = AdverseRecallReview.FeedbackChoices.choices 
    if request.method == "POST":
        recall = AdverseRecallReview.objects.filter(id=id).first()
        state = request.POST.get("state")
        recall.state = state
        recall.save()
    
    recall = AdverseRecallReview.objects.filter(id=id).first()
    context = {"recall": recall, "state_choices": state_choices}
    return render(request, "client_portal/recall_details.html", context)

def article_details(request, id):
    state_choices = ArticleReview.ArticleReviewState.choices 
    
    if request.method == "POST":
        article = ArticleReview.objects.filter(id=id).first()
        state = request.POST.get("state")
        article.state = state
        article.save()

    article = ArticleReview.objects.filter(id=id).first()
    context = {"article": article, "state_choices": state_choices}
    return render(request, "client_portal/article_details.html", context)


def automated_search(request):
    return render(request, "client_portal/automated_search.html")

def create_automated_search(request):
    return render(request, "client_portal/create_automated_search.html")

def automated_search_results(request,id):
    # auto_search_id = kwargs.get("id")
    automated_search = AutomatedSearchProject.objects.filter(id=id).first()
    articles = Article.objects.all()[0:4]

    context  =  {
        "automated_search": automated_search,
        "articles": articles

    }

    return render(request, "client_portal/automated_search_results.html",context)


def automated_search_update(request,id):
    automated_search = AutomatedSearchProject.objects.filter(id=id).first()
    context  =  {
        "automated_search": automated_search,
    }
    return render(request, "client_portal/update_automated_search.html",context)

from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
import csv
def export_automated_search_results(request,id):
    try:
        automated_search = AutomatedSearchProject.objects.filter(id=id).first()

        if automated_search is None:
            return Response({"error message": "Automated search not found."}, status=status.HTTP_404_NOT_FOUND)

        articles = Article.objects.filter(literature_review=automated_search.lit_review)

        # Prepare the CSV data
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="exported_articles.csv"'

      
        writer = csv.writer(response)
        # Write the header row 
        header_row = ["Article Id", "Title", "Abstract", "Citation", "Pubmed UID", "PMC UID", "FullText", "Publication Year"]
        writer.writerow(header_row)

        # Write data rows for each article
        for article in articles:
            data_row = [article.id, article.title, article.abstract, article.citation, article.pubmed_uid, article.pmc_uid, article.full_text, article.publication_year]
            writer.writerow(data_row)
        return response
    except Exception as e:
        error_message = str(e)
        return Response({"error message": error_message}, status=status.HTTP_400_BAD_REQUEST)


