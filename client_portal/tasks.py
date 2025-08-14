from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from .utils import get_users, send_mail
from backend import settings
from django.core.files import File
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from backend.logger import logger

from client_portal.helpers import create_terms_for_autosearch, construct_chart_image

from lit_reviews.tasks import send_email
from lit_reviews.models import ArticleReview, LiteratureReview, LiteratureSearch
from lit_reviews.report_builder.all_articles_reviews import generate_excel_context
from lit_reviews.helpers.reports import create_excel_file

User = get_user_model()


@shared_task()
def send_create_notification(deliverable_id):
    """Send email with mailgun"""
    subject_template_name = "client_portal/deliverable_create_subject.txt"
    email_template_name = "client_portal/deliverable_create_email.html"
    from_email = None
    extra_email_context = None

    from .models import Deliverable

    deliverable = Deliverable.objects.filter(pk=deliverable_id).first()

    if deliverable:
        email = deliverable.project.client.email
        email_field_name = User.get_email_field_name()
        for user in get_users(email):
            user_email = getattr(user, email_field_name)
            context = {
                "deliverable": deliverable,
                "user": user,
                **(extra_email_context or {}),
            }
            send_mail(
                subject_template_name,
                email_template_name,
                context,
                from_email,
                user_email,
            )


@shared_task()
def create_terms_for_automated_searches_cronjob():
    from client_portal.models import AutomatedSearchProject

    auto_search_projects = AutomatedSearchProject.objects.all()
    for auto_search_project in auto_search_projects:
        new_searches = []
        searches = create_terms_for_autosearch(
            auto_search_project.databases_to_search.all(), 
            [auto_search_project.terms], 
            auto_search_project.lit_review, 
            auto_search_project.start_date.strftime("%Y-%m-%d"), 
            auto_search_project.interval,
            str(auto_search_project.client),
        ) 
        new_searches = [*new_searches, *searches]

        if len(new_searches):
            email_automated_search_results(new_searches, auto_search_project.id)


@shared_task()
def create_terms_for_automated_searches_initial(selected_dbs, search_term, lit_review_id, start_date, selected_interval, client, automated_search_id):
    """
    This will be executed when the search is created.
    """
    lit_review = LiteratureReview.objects.get(id=lit_review_id)
    new_searches = create_terms_for_autosearch(
        selected_dbs, 
        [search_term], 
        lit_review, 
        start_date, 
        selected_interval, 
        client,
    ) 
    if len(new_searches):
        email_automated_search_results(new_searches, automated_search_id)


@shared_task()
def email_automated_search_results(new_searches, automated_search_id):
    from client_portal.models import  AutomatedSearchExcelReport, AutomatedSearchProject
    
    automated_search = AutomatedSearchProject.objects.get(id=automated_search_id)
    search_summary = []
    searches_ids = []
    for search in new_searches:
        search_summary.append({
            "id": search.id,
            "search_term": search.term,
            "db": search.db.name,
            "count": ArticleReview.objects.filter(search=search).count(),
            "dates": search.start_search_interval.strftime("%Y-%m-%d") + " to " + search.end_search_interval.strftime("%Y-%m-%d")
        })
        searches_ids.append(search.id)

    article_reviews = ArticleReview.objects.filter(search__id__in=searches_ids)
    rows_list = generate_excel_context(article_reviews)
    if len(rows_list):
        document_name_csv    =  "{0} {1}.csv".format(search_summary[0]["search_term"], search_summary[0]["dates"])
        document_name_excel  =  "{0} {1}.xlsx".format(search_summary[0]["search_term"], search_summary[0]["dates"])
        document_path_final_excel = create_excel_file(1, 1, document_name_csv, document_name_excel, rows_list)
        file = open(document_path_final_excel, "rb")
        automated_search_summary_file = AutomatedSearchExcelReport.objects.create(
            file=File(file)
        )

        ### CREATE DATA FOR CHARTS ####  
        all_searches = LiteratureSearch.objects.filter(literature_review__id=automated_search.lit_review.id)
        dates = [search.start_search_interval.strftime("%Y-%m-%d") + " to " + search.end_search_interval.strftime("%Y-%m-%d") for search in all_searches]
        values = [ArticleReview.objects.filter(search=search).count() for search in all_searches]
        chart_title = "Result Counts Trending"
        chart_x_label = "Date Ranges"
        chart_y_label = "Results Count"
        file_name = "automated_search_chart_" + str(timezone.now()) + ".png"

        with open("/tmp/" + str(file_name), "wb") as tmp_f:
            construct_chart_image(dates, values, chart_title, chart_x_label, chart_y_label, tmp_f, type="bar")

        file_temp = open("/tmp/" + str(file_name), "rb")
        chart_png = File(file_temp)
        automated_search_chart = AutomatedSearchExcelReport.objects.create(
            image=chart_png,
            type="IMAGE"
        )
        file_temp.close()

        context = {
            "search_summary": search_summary,
            "results_excel_url": automated_search_summary_file.file.url,
            "device_name": automated_search.lit_review.device.name,
            "manufacturer_name": automated_search.lit_review.device.manufacturer.name,
            "chart_png": automated_search_chart.image.url,
        }
        logger.info("Email is sent to client for Automated Searches")

        subject = 'CIteMed.io Clinical Literature Alerts'
        template = "email/automated_searches_summary.html"
        if settings.ENV == "PROD":
            User = get_user_model()
            user = User.objects.get(client=automated_search.client)
            recipient_email = [user.email]
        else:
            if settings.SUPPORT_EMAILS:
                recipient_email = settings.SUPPORT_EMAILS
            else:
                recipient_email = [settings.DEFAULT_FROM_EMAIL]
        
        # Render the email template with the given context
        email_body = render_to_string(template, context)

        # Create the EmailMessage object
        email = EmailMessage(subject, email_body, to=recipient_email)
        email.content_subtype = 'html'  # Set the content type to HTML
        
        # Optionally, you can attach files or set additional headers
        
        # Send the email
        email.send()


@shared_task()
def automated_search_notify_support_team(message, link):
    subject = "New Automated Search Created"
    send_email(subject, message, to=settings.SUPPORT_EMAILS, link=link)
