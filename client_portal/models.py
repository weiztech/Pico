from venv import create
from django.db import models
from django.db.models.deletion import CASCADE, DO_NOTHING
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib import admin

from backend.logger import logger
from lit_reviews.models import Article, LiteratureReview, Client, NCBIDatabase

User = get_user_model()

######################################################################
# Deprecated 23-11-2024 below models LibraryEntry no longer used ####
#####################################################################
class LibraryEntry(models.Model):
    article = models.OneToOneField(Article, on_delete=CASCADE, related_name="library_entry")
    is_hidden = models.BooleanField(default=False, blank=False)
    projects = models.ManyToManyField("Project", related_name="library_entries")

    def __str__(self):
        return f"Article ID : {self.article.id}"
####################################################################

class Project(models.Model):
    # TODO: Is delete user?
    project_name = models.CharField(max_length=100,null=False, blank=False,default="project name")
    client = models.ForeignKey(Client, on_delete=CASCADE)
    type_choices = (
        ("lit_review", "Lit. Review"),
        ("CER", "CER"),
        ("PMCF", "PMCF"),
        ("Vigilance", "Vigilance"),
        ("Custom", "Custom"),
    )
    type = models.CharField(max_length=32, choices=type_choices, default="lit_review")
    initial_complated_date = models.DateField(null=True, blank=True)
    renewal_interval = models.IntegerField(null=False, blank=False, default=1)
    most_recent_project = models.ForeignKey(
        "self", on_delete=DO_NOTHING, null=True, blank=True
    )
    lit_review = models.ForeignKey(LiteratureReview, on_delete=DO_NOTHING)
    share_drive_url = models.URLField(null=True, blank=True)
    max_terms = models.IntegerField(default=15)
    max_hits = models.IntegerField(default=500)
    max_results = models.IntegerField(default=50)

    def __str__(self) -> str:
        return f"{self.project_name} - {self.client} - {self.lit_review.device}"


class Action(models.Model):
    project = models.ForeignKey(Project, on_delete=DO_NOTHING)
    date_sent = models.DateField(auto_now_add=True)
    message = models.TextField()
    type_choices = (
        ("message", "message"),
        ("renewal", "renewal"),
        ("vigilance", "vigilance"),
        ("alert", "alert"),
    )
    type = models.CharField(max_length=32, choices=type_choices, default="message")
    resolved_status_choices = (
        ("read", "read"),
        ("unread", "unread"),
        ("hidden", "hidden"),
    )
    resolved_status = models.CharField(
        max_length=30, choices=resolved_status_choices, default="unread"
    )


class Deliverable(models.Model):
    project = models.ForeignKey(Project, on_delete=DO_NOTHING)
    file = models.FileField(null=False, blank=False)
    version_short_name = models.CharField(max_length=32, editable=False, default=0)
    previous = models.ForeignKey("self", on_delete=DO_NOTHING, null=True, blank=True)
    date = models.DateField(auto_now=True)
    comments = models.TextField()
    comments_revision_file = models.FileField(null=True, blank=True)
    status_choices = (
        ("final", "final"),
        ("draft", "draft"),
        ("pending_client_feedback", "pending client feedback"),
        ("pending_corrections", "pending corrections"),
    )
    status = models.CharField(max_length=32, choices=status_choices, default="draft")

    def __str__(self) -> str:
        return f"{self.project} - {self.status} - v.{self.version_short_name}"

    def save(self, *args, **kwargs):
        from client_portal.tasks import send_create_notification

        # start with version 0 and increment it for each Deliverable
        current_version_short_name = (
            Deliverable.objects.filter(id=self.id)
            .order_by("-version_short_name")
            .first()
        )
        if current_version_short_name:
            self.version_short_name = (
                int(current_version_short_name.version_short_name) + 1
            )
            self.previous = (
                Deliverable.objects.filter(id=self.id)
                .order_by("-version_short_name")
                .first()
            )
            Deliverable.__init__(
                self,
                project=self.project,
                file=self.file,
                version_short_name=self.version_short_name,
                previous=self.previous,
                date=self.date,
                comments=self.comments,
                comments_revision_file=self.comments_revision_file,
                status=self.status,
            )
            logger.info("Create new version deliverable: {}", self)

        super(Deliverable, self).save(*args, **kwargs)
        logger.info("Create deliverable: {}", self)
        send_create_notification.delay(self.id)



class AutomatedSearchProject(models.Model):
    lit_review = models.ForeignKey(LiteratureReview, on_delete=DO_NOTHING)
    client = models.ForeignKey(Client, on_delete=CASCADE)
    status_choices = (
        ("completed", "completed"),
        ("pending", "pending"),
        ("cancelled", "cancelled"),
    )
    status = models.CharField(max_length=32, choices=status_choices, default="pending")
    last_run_date = models.DateField(auto_now=True)
    start_date = models.DateField(auto_now=True)
    interval_choices = (
        ("weekly", "weekly"),
        ("monthly", "monthly"),
        ("quarterly", "quarterly"),
        ("annually", "annually"),
    )
    interval = models.CharField(max_length=32, choices=interval_choices, default="weekly")
    terms = models.CharField(max_length=1000,null=True, blank=True)
    terms_file = models.FileField(null=True, blank=True)
    databases_to_search = models.ManyToManyField(NCBIDatabase, blank=True)

    def __str__(self) -> str:
        return f"Automated Search Project - {self.lit_review}"

class ArticleComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_time = models.DateTimeField(auto_now_add=True)
    text  = models.CharField(max_length=1000)
    article = models.ForeignKey(Article, on_delete=CASCADE)

    def __str__(self) -> str:
        return f"ArticleComment - {self.article}"


# Just a place holder for excel reports generated after automated searches auto execution
class AutomatedSearchExcelReport(models.Model):
    CHOICES = [
        ("IMAGE", "IMAGE"),
        ("EXCEL", "EXCEL")
    ]

    file = models.FileField(null=True)
    image = models.ImageField(null=True)
    type = models.CharField(choices=CHOICES, default="EXCEL", max_length=26)
    created_at = models.DateTimeField(default=timezone.now)


# Register Models to Admin Dashboard 
from django import forms

class ProjectForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        
        super (ProjectForm,self ).__init__(*args,**kwargs) # populates the post
        self.fields['lit_review'].queryset = LiteratureReview.objects.filter(is_archived=False)

    class Meta:
        from client_portal.models import Project
        model = Project
        fields = "__all__"

class ProjectAdmin(admin.ModelAdmin):
    model = Project
    search_fields = ['project_name']
    # autocomplete_fields = ['lit_review']
    form = ProjectForm


admin.site.register(Action)
admin.site.register(Project, ProjectAdmin)
admin.site.register(AutomatedSearchProject)
admin.site.register(ArticleComment)
admin.site.register(AutomatedSearchExcelReport)