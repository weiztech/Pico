from django.shortcuts import get_object_or_404 
from django.core import mail
from django.template.loader import render_to_string
from django.urls import reverse

from django.conf import settings
from backend.logger import logger
from lit_reviews.helpers.generic import (
    get_server_env, 
)
from client_portal.utils import send_mail as client_send_mail
from django.contrib.auth import get_user_model
from lit_reviews.models import (
    LiteratureReview,
    Comment,
)

User = get_user_model()
READ_BUF_SIZE = 4096


def send_email_when_comment_created_task(lit_review_id, comment_id, domain_name):
    subject_template_name = "email/add_comment_mail_template.txt"
    email_template_name = "email/mail_template.html"
    from_email = settings.DEFAULT_FROM_EMAIL

    lit_review = get_object_or_404(LiteratureReview, pk=lit_review_id)    
    users = User.objects.filter(client__id=lit_review.client.id)

    comment = Comment.objects.get(id=comment_id)
    article_id = comment.article_review.article.id
    article_title = comment.article_review.article.title
    project = project = lit_review.project_set.all().first()
    article_link =  reverse("lit_reviews:article_review_detail", kwargs={"id": lit_review_id, "article_id": article_id})        
    article_review_link = domain_name + article_link[1:]
    
    subject = f"A comment has been added"
    message = """
    A comment has been added for article title: {}
    inside project: {} 
    click <a href="{}">here </a>to review it".        
    """.format(article_title, project.project_name,article_review_link)
    
    for user in users:
        email_field_name = User.get_email_field_name()
        user_email = getattr(user, email_field_name)
        context = {
                "subject": subject,
                "message": message,
            }
        
        logger.debug(f"Sending comment email to user {user_email}")
        client_send_mail(
            subject_template_name,
            email_template_name,
            context,
            from_email,
            user_email,
        )


def send_error_email_task(report, project, client_name, client_email, error_track):
    """
    Send email to support team if an error occured during handeling a specific task.
    """
    
    env = get_server_env()
    subject = "Error Occured While Generating a Report"
    message = """
    Error occured while trying to create {} More info can be found below:
    
    Environment: {}. \n
    Project: {}. \n
    Client Name: {}. \n
    Client Email: {}. \n
    Error: {}. \n 
    """.format(report, env, project, client_name, client_email, error_track)
    send_email_task(subject, message, to=settings.SUPPORT_EMAILS)


def send_email_task(subject, message, to=[], link=None, is_error=False ,error="", from_email=None):
    """Send email"""
    subject = subject.encode("utf-8", "ignore").decode("utf-8")
    message = message.encode("utf-8", "ignore").decode("utf-8")

    if is_error:
        html_message = render_to_string('email/mail_template.html', {'subject': subject, "message": message, "error": error})
    else:
        html_message = render_to_string('email/mail_template.html', {'subject': subject, "message": message, "link": link})
        
    # plain_message = strip_tags(html_message)
    from_email = from_email if from_email else settings.DEFAULT_FROM_EMAIL
    mail.send_mail(subject, html_message, from_email, to, html_message=html_message)