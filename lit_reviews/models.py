import os 
import re
import uuid
import json
import time
from PIL import Image 
from io import BytesIO
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from django.db.models import Q
from django.contrib.postgres.fields import HStoreField
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from backend.logger import logger
from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.files import File

from lit_reviews.constants import RIS_FILE_FIELDS


User = get_user_model()

class NonDeletedLiteratureReviewsManager(models.Manager):
    def get_queryset(self):
        # Override the get_queryset method to filter out deleted objects
        return super().get_queryset().filter(is_deleted=False)
    
class ProjectConfig(models.Model):
    MODES = (
        ("B","Basic"),
        ("A","Advanced")
    )
    project = models.ForeignKey("client_portal.Project", on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    sidebar_mode = models.CharField(choices=MODES, max_length=126, default="B")

    @property
    def count_client_projects(self):
        project = self.project
        lit_review = project.lit_review
        if lit_review.client:
            return LiteratureReview.objects.filter(client=lit_review.client).count()
        else:
            return LiteratureReview.objects.all().count()

    @property
    def is_new_project(self):
        if self.count_client_projects > 2:
            return False 
        return True

class Reviewer(models.Model):
    first_name = models.TextField()
    last_name = models.TextField()
    credentials = models.TextField(null=True, blank=True)
    display_override = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.display_override:
            return self.display_override
        credentials = f", {self.credentials}" if self.credentials else ""
        return f"{self.first_name} {self.last_name}{credentials}"



class Client(models.Model):
    name = models.TextField(unique=True)
    short_name = models.TextField()
    long_name = models.TextField()
    full_address_string = models.TextField()
    logo = models.ImageField(null=True, blank=True)
    is_company = models.BooleanField(
        "Citemed.io customer",
        default=True,
        help_text="If the client is a company multiple citemed users can be attached to his company",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        init_logo = self.logo
        try:
            if getattr(self, 'logo_changed', True):
                logo = Image.open(self.logo)
                new_logo = logo.resize((250, 180), Image.ANTIALIAS)
                new_image_io = BytesIO()
                
                try:
                    img_format = os.path.splitext(self.logo.name)[1][1:].upper()
                    img_format = 'JPEG' if img_format == 'JPG' else img_format
                except:
                    img_format = 'JPEG'

                new_logo.save(new_image_io, format=img_format)
                temp_name = self.logo.name
                self.logo.delete(save=False)  

                self.logo.save(
                    temp_name,
                    content=ContentFile(new_image_io.getvalue()),
                    save=False
                )
            return super(Client, self).save(*args, **kwargs)

        except Exception as error:
            print("Failed to resize image, ", error)
            self.logo = init_logo
            return super(Client, self).save(*args, **kwargs)

class Manufacturer(models.Model):

    name = models.TextField(unique=True)

    def __str__(self):
        return self.name


class Device(models.Model):

    name = models.CharField(max_length=150)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.DO_NOTHING)
    classification = models.CharField(max_length=100)
    markets = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.name} - {self.manufacturer}"


# class LiteratureReviewIntake(models.Model):

#     client = models.ForeignKey(Client, on_delete=models.DO_NOTHING)
#     device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
#     markets = models.TextField()


#     def __str__(self):
#         return f"{self.device} - {self.client}"


class LiteratureReview(models.Model):
    TYPES = [
        ("STANDARD", "Standard"),
        ("SIMPLE", "Streamline")
    ]
    client = models.ForeignKey(Client, verbose_name="Company", on_delete=models.DO_NOTHING)
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING, null=True, blank=True)
    #intake = models.OneToOneField(LiteratureReviewIntake, on_delete=models.DO_NOTHING)
    is_archived = models.BooleanField(default=False) # Completed
    is_autosearch = models.BooleanField(default=False, help_text="Auto Search Project are only for testing different search terms and check thier results")
    is_notebook = models.BooleanField(default=False, help_text="A notebook Project are only for testing different search terms and check thier results, we should have one notebook project per client")
    authorized_users = models.ManyToManyField(User, help_text="Want to make this project accessible to external users that are not a company members? you can add them here", null=True, blank=True)
    review_type = models.CharField(choices=TYPES, max_length=126, default="STANDARD")

    # created for a living review ?
    is_living_review = models.BooleanField(default=False)
    parent_living_review = models.ForeignKey(
        "LivingReview", 
        null=True, blank=True, 
        on_delete=models.SET_NULL, 
        help_text="was this created automatically for a living review?", 
        related_name="projects"
    )

    # have we copy data from another project ? and was it successful ?
    cloned_from = models.ForeignKey("LiteratureReview", null=True, blank=True, on_delete=models.SET_NULL)
    is_cloning_completed = models.BooleanField(default=True)
    cloning_errors = models.TextField(null=True, blank=True, help_text="if the clone fails store any errors here")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, default=timezone.now)

    # Replace default objects manager with a custom manager to get only non deleted records
    objects = NonDeletedLiteratureReviewsManager()
    all_objects = models.Manager()

    def __str__(self):
        project = self.project_set.all().first()
        if self.is_living_review_project and self.searchprotocol:
            start_date = self.searchprotocol.lit_start_date_of_search
            end_date = self.searchprotocol.lit_date_of_search
            return f"{self.device} - {self.parent_living_review.interval} ({start_date} => {end_date})" 

        if self.review_type == "STANDARD":
            if project:
                return f"{project.project_name} - {self.device} - {self.client}"
            else:
                return f"{self.device} - {self.client}"
        else:
            if project:
                return f"{project.project_name} - {self.client}"
            else:
                return f"Simple Review for {self.client}"
            
    def get_absolute_url(self):
        return reverse(
            "literature_reviews:literature_review_detail", args=[str(self.id)]
        )

    @property
    def is_living_review_project(self):
        return True if self.parent_living_review else False


    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):  
        is_create = True if self.pk is None else False      
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        SearchProtocol.objects.get_or_create(literature_review=self)
        
        if is_create:
            logger.info("create init literature review search parameters for scrapers")
            from lit_reviews.helpers.search_terms import create_init_search_params_litreview
            create_init_search_params_litreview(self)

            ex1 = ExclusionReason.objects.create(
                literature_review=self,
                reason="Articles unrelated to the device of interest, an equivalent device, similar device, accessory, or device component relevant to device",
            )
            ex2 = ExclusionReason.objects.create(
                literature_review=self,
                reason="Algorithm, simulations or bench test relevant to the device of interest or an equivalent device but not in a scientifically validated method/methodology",
            )
            ex3 = ExclusionReason.objects.create(
                literature_review=self,
                reason="Non-peer reviewed articles (e.g. letters to editor, opinions, editorials, press releases, advertisements, books, dissertations, thesis)",
            )
            ex4 = ExclusionReason.objects.create(
                literature_review=self,
                reason="Conference abstracts or proceedings, posters (unless previously unknown benefits, risks/complications are reported)",
            )
            ex5 = ExclusionReason.objects.create(
                literature_review=self,
                reason="Non-human studies (e.g. in vitro, in vivo, animal, cadaver, phantom studies, simulations) that is not acceptable data for safety or performance.",
            )

            kw = KeyWord.objects.create(
                literature_review=self,
                exclusion="rats, rat , pig , pigs , monkey, primate, cow,  pre-clinical, cadaver, preclinical, porcine, cynomolgus, rodent, marsupials, binding, ex vivo, murine, canine, dogs, drosophila, insect, crustacea, marine, zebra, animal",
                population="adults",
                intervention="citemed",
                comparison="citemed",
                outcome="citemed",
            )

            # TODO: Create Default ExtractionFields
            from lit_reviews.helpers.extraction_fields import create_and_link_default_extraction_fields
            create_and_link_default_extraction_fields(self)


class KeyWord(models.Model):

    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    population = models.TextField(null=True, blank=True)
    intervention = models.TextField(null=True, blank=True)
    comparison = models.TextField(null=True, blank=True)
    outcome = models.TextField(null=True, blank=True)
    exclusion = models.TextField(null=True, blank=True)
    population_color = models.TextField(null=True, blank=True,default="#ebe4c2")
    intervention_color = models.TextField(null=True, blank=True,default="#d5cad0")
    comparison_color = models.TextField(null=True, blank=True,default="#c7d7cf")
    outcome_color = models.TextField(null=True, blank=True,default="#aec2d0")
    exclusion_color = models.TextField(null=True, blank=True,default="#ff0000")

class CustomKeyWord(models.Model):
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    custom_kw = models.TextField(null=True, blank=True)
    custom_kw_color = models.TextField(null=True, blank=True, default="#ffffff")


class SearchProtocol(models.Model):
    ########## Device Description AND Use #########
    literature_review = models.OneToOneField(LiteratureReview, on_delete=models.CASCADE)
    device_description = models.TextField(null=True, blank=True)
    intended_use = models.TextField(null=True, blank=True)
    indication_of_use = models.TextField(null=True, blank=True)
    
    ########### Date Range Of Search #############
    lit_date_of_search = models.DateField(null=True, blank=True) # End date of search
    ae_date_of_search = models.DateField(null=True, blank=True) # End date of search
    lit_start_date_of_search = models.DateField(null=True, blank=True)
    ae_start_date_of_search = models.DateField(null=True, blank=True)

    years_back = models.IntegerField(null=True, blank=True)
    ae_years_back = models.IntegerField(null=True, blank=True)

    #############  Search Results Limit #########
    max_imported_search_results = models.IntegerField(default=300)
    lit_searches_databases_to_search = models.ManyToManyField("NCBIDatabase", related_name="searchprotocol_lit_searches")
    ae_databases_to_search = models.ManyToManyField("NCBIDatabase", related_name="searchprotocol_ae", blank=True)

    ######### Similar Device and State of the Art #############
    comparator_devices = models.TextField(null=True, blank=True)
    sota_description = models.TextField(null=True, blank=True, default="[Device Name] (and associated components) as [to be filled in]. would be compared to the state-of-the-art (SoTA) [to be filled in]. (Or devices most commonly used to [intended use]).  A separate SoTA search would include the use of standard [to be filled in].")
    sota_product_name = models.CharField(max_length=256, null=True, blank=True)

    ########### Claims ###############
    safety_claims = models.TextField(null=True, blank=True)
    performance_claims = models.TextField(null=True, blank=True)
    other_info = models.TextField(null=True, blank=True)
    
    ############# Scope of the Review ################
    scope = models.TextField(null=True, blank=True, default="The scope of the literature search includes a query of select adverse event report databases as well as scientific databases for the date range starting from [startdate] to [end date]. This period of time is felt to provide sufficient clinical experience with these devices from both a safety and performance perspective. Performance assessments include reports designed to....[ finish the paragraph below ]")

    ########### Miscellaneous ##########
    preparer = models.CharField(max_length=256, null=True, blank=True, default="S. Senthil Kumar, Ph.D.")


    ############ VIGILANCE & PMCF Related Fields #############
    vigilance_inclusion_manufacturers = models.TextField(null=True, blank=True)
    vigilance_inclusion_keywords = models.TextField(null=True, blank=True)

    ########### No Longer Used ############
    max_result_count = models.IntegerField(null=True, blank=True)
    max_articles_reviewed = models.IntegerField(null=False, blank=False,default=100)
    begin_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"SearchProtocol({str(self.literature_review)})"


class ExclusionReason(models.Model):
    literature_review = models.ForeignKey(
        LiteratureReview, on_delete=models.CASCADE, related_name="exclustion_reasons"
    )
    reason = models.TextField(null=False, blank=False, max_length=2000)


class EquivalentDevice(models.Model):
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
    equivalent_to = models.ForeignKey(
        Device, on_delete=models.DO_NOTHING, related_name="equivalent_to"
    )


class NCBIDatabase(models.Model):
    name = models.TextField(unique=True, primary_key=True)
    entrez_enum = models.CharField(max_length=30)
    displayed_name = models.CharField(max_length=126, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    is_ae = models.BooleanField(null=True, blank=True)
    is_recall = models.BooleanField(blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    search_strategy = models.TextField(null=True, blank=True)
    is_archived = models.BooleanField(default=False, help_text="Archived datrabase are not being used any more")
    is_external = models.BooleanField(default=False, help_text="external databases are not supported by citemed and only available for direct citation imports")
    instructions_for_search = models.URLField(null=True, blank=True)
    export_file_format = models.CharField(
        max_length=256, null=True, blank=True, 
        help_text="File format for the search results exported file to be uploaded in the app"
    )
    auto_search_available = models.BooleanField(default=False, help_text="Auto Search Scraper available in this database ?")

    def __str__(self):
        name = self.displayed_name if self.displayed_name else self.name
        return name

class LiteratureReviewSearchProposal(models.Model):
    report = models.ForeignKey("LiteratureReviewSearchProposalReport", related_name="search_proposal", null=True, on_delete=models.SET_NULL)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    literature_search = models.OneToOneField("LiteratureSearch", null=True, on_delete=models.CASCADE)
    in_abstract = models.BooleanField(default=True)
    full_text_available = models.BooleanField(default=True)
    is_sota_term = models.BooleanField(default=None,null=True, blank=True)
    db = models.ForeignKey(NCBIDatabase, on_delete=models.DO_NOTHING)
    term = models.CharField(max_length=5000)
    years_back = models.FloatField(default=10)
    result_count = models.IntegerField(null=True)
    search_label = models.CharField(default=None, blank=True, null=True, max_length=50)

    class DateType(models.TextChoices):
        publication = "pdat", _("Publication Date")
        entrez = "edat", _("Entrez Date")

    datetype = models.CharField(
        max_length=10, choices=DateType.choices, default=DateType.publication
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["literature_review", "term", "db"],
                name="unique_review_term",
            )
        ]

    def __str__(self):
        return f"{self.term} - {self.db}"

    def as_entrez_dict(self):
        db = self.db.entrez_enum
        term = self.term
        # if self.in_abstract:
        #     abstract_field = ABSTRACT_FIELD[db]
        #     term = f"{term}[{abstract_field}]"
        # if self.full_text_available:
        #     term = f"{term} AND free fulltext[filter]"
        return dict(
            db=db,
            term=term,
            reldate=int(self.years_back * 365),
            datetype=self.datetype,
        )

    def save(self, *args, **kwargs):
        self.term = self.term.strip()
        super(LiteratureReviewSearchProposal, self).save(*args, **kwargs)


class LiteratureReviewSearchProposalReport(models.Model):
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    term = models.CharField(max_length=5000)
    errors = models.TextField(null=True)
    status_choices = (
        ("UPDATED", "UPDATED"),
        ("FETCHING_PREVIEW", "FETCHING_PREVIEW"),
        ("PROCESSING", "PROCESSING"),
        ("FAILED", "FAILED"),
    )
    status = models.CharField(
        max_length=30, choices=status_choices, default="UPDATED"
    )  
    updated_at = models.DateTimeField(auto_now=True)

# class LiteratureReviewProject(models.Model):
#     """
#     Things more related to the LiteratureReview as a project than to the review itself
#     """

#     literature_review = models.OneToOneField(LiteratureReview, on_delete=models.CASCADE)
#     start_date = models.DateField()
#     due_date = models.DateField()

#     def __str__(self):
#         return f"{self.start_date} - {self.literature_review}"


class AdverseEvent(models.Model):
    db = models.ForeignKey(
        NCBIDatabase, on_delete=models.CASCADE, null=True, blank=True
    )
    event_uid = models.TextField(null=True, blank=True)
    event_type = models.CharField(max_length=50, null=True, blank=True)

    event_number_full = models.CharField(max_length=150, null=True, blank=True)
    event_number_short = models.CharField(max_length=150, null=True, blank=True)

    description = models.TextField(null=True, blank=True)
    manufacturer = models.TextField(null=True, blank=True)
    brand_name = models.CharField(max_length=150, null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    report_date = models.DateField(null=True, blank=True)
    manual_type = models.CharField(max_length=112, null=True, blank=True)
    manual_severity = models.CharField(max_length=112, null=True, blank=True)
    manual_link = models.URLField(max_length=1024, null=True, blank=True)
    manual_pdf = models.FileField(null=True, blank=True)
    event_number_full = models.CharField(max_length=150, null=True, blank=True)
    event_number_short = models.CharField(max_length=150, null=True, blank=True)
    
class AdverseRecall(models.Model):
    db = models.ForeignKey(
        NCBIDatabase, on_delete=models.CASCADE, null=True, blank=True
    )
    event_uid = models.TextField(null=True, blank=True)
    product_description = models.TextField(null=True, blank=True)
    recall_class = models.IntegerField(null=True, blank=True)
    trade_name = models.TextField(null=True, blank=True)
    firm_name = models.TextField(null=True, blank=True)
    recall_reason = models.TextField(null=True, blank=True)
    event_date = models.DateField(null=True, blank=True)
    manual_type = models.CharField(max_length=112, null=True, blank=True)
    manual_severity = models.CharField(max_length=112, null=True, blank=True)
    manual_link = models.URLField(max_length=1024, null=True, blank=True)
    manual_pdf = models.FileField(null=True, blank=True, upload_to="media")


class LiteratureSearch(models.Model):
    """
    Many LiteratureSearches per LiteratureReview
    """
    class PicoCategory(models.TextChoices):
        POPULATION = "P", _("Population")
        INTERVENTION = "I", _("Intervention")
        COMPARISON = "C", _("Comparison")
        OUTCOME = "O", _("Outcome")
        
    status_choices = (
        ("COMPLETE", "COMPLETE"),
        ("INCOMPLETE-ERROR", "INCOMPLETE-ERROR"),
        ("NOT RUN", "NOT RUN"),
        ("RUNNING", "RUNNING"),
    )

    time_performed = models.DateTimeField(auto_now_add=True)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    db = models.ForeignKey(
        NCBIDatabase, on_delete=models.DO_NOTHING, default="PubMed Central"
    )
    term = models.CharField(max_length=5000)
    is_sota_term = models.BooleanField(default=None, blank=True, null=True)
    is_archived = models.BooleanField(default=False, blank=True, null=True)
    import_status = models.CharField(max_length=30, choices=status_choices, default="NOT RUN")  # comes from import script
    pico_category = models.CharField(
        max_length=1, choices=PicoCategory.choices, null=True, blank=True
    )

    # configuration fields
    search_label = models.CharField(default=None, blank=True, null=True, max_length=50)
    result_count = models.IntegerField(null=True, blank=True)
    expected_result_count = models.IntegerField(null=True, blank=True)
    advanced_options = HStoreField(
        null=True,
        blank=True,
        help_text="""
            Storing Extra searching parameters that are specific per each field below list of params:
            1. search_field: for clinical trials and maude we can search using different fields rather 
            than just a term text query, the default is the term query for clinical trials and product code for maude.
        """
    )

    ## Search Dashboard fields (post search run details)
    search_file = models.FileField(null=True, blank=True)
    search_file_url = models.URLField(null=True, blank=True, max_length=1024)
    disable_exclusion = models.BooleanField(default=False)
    processed_articles = models.IntegerField(
        null=True, blank=True
    )  # comes from import script
    imported_articles = models.IntegerField(
        null=True, blank=True
    )  # comes from import script
    duplicate_articles = models.IntegerField(
        null=True, blank=True
    )  # comes from import script
    

    # Less important fields
    script_time = models.DateTimeField(null=True, blank=True, default=None)
    ae_events = models.ManyToManyField(
        AdverseEvent, related_name="ae_events", blank=True
    )
    ae_recalls = models.ManyToManyField(
        AdverseRecall, related_name="ae_recalls", blank=True
    )
    error_msg = models.TextField(null=True, blank=True)
    created_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    search_report = models.FileField(
        null=True, blank=True, 
        help_text="Search Report is a zip file that contains search_file & the datanase instructions for a manual search"
    )
    search_report_failing_msg = models.CharField(
        null=True, blank=True, 
        max_length=1024,
        help_text="If Search Report Generation fails the error message will bestored here"
    )    
    in_abstract = models.BooleanField(default=False)
    full_text_available = models.BooleanField(default=False)
    years_back = models.FloatField(default=10) # not used any more the date range will be coming from the SearchProtocol

    # Below fields will be only used for automated searhes or notebook searches
    is_notebook_search = models.BooleanField(default=False, blank=True, null=True)
    start_search_interval = models.DateField(null=True, blank=True)
    end_search_interval = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["literature_review", "term", "db", "start_search_interval"],
                name="unique_term_source",
            ),
            # if start_search_interval is None, take only review - term - db into consideration as a unique constraint
            models.UniqueConstraint(
                fields=["literature_review", "term", "db"],
                condition=Q(start_search_interval__isnull=True),
                name="unique_term_source2",
            )
        ]

    @property 
    def not_run_or_excluded(self):
        return ( self.import_status == "NOT RUN" or self.result_count == -1)

    @property 
    def is_ae_not_maude(self):
        is_ae = self.db.is_ae or self.db.is_recall
        not_fda = "maude" not in self.db.entrez_enum
        return is_ae and not_fda

    @property 
    def is_completed(self):
        status_completed = self.import_status == "COMPLETE"
        return (status_completed or self.none_excluded or self.limit_excluded)
    
    @property 
    def none_excluded(self):
        """ Excluded with 0 results """
        if self.result_count is not None:
            return self.result_count == 0

        return False 

    @property 
    def limit_excluded(self):
        """ Excluded because limit exceeded """
        IMPORTED = self.imported_articles if self.imported_articles else 0
        PROCCESSED = self.processed_articles if self.processed_articles else 0
        RESULT_COUNT = self.result_count if self.result_count else 0
        return RESULT_COUNT > 0 and IMPORTED == 0 and PROCCESSED == 0  
    
    def __str__(self):
        return f"{self.term} - {self.db}"
    
    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        self.term = self.term.strip()
        ## on save, check if there is a SearchReviewProposal obj
        ## that has same term and lit review id.  if yes, then update sota field.

        props = LiteratureReviewSearchProposal.objects.filter(
            literature_review=self.literature_review, term__iexact=self.term
        )
        if props.count() > 0:
            print("UPDATING SOTA TERM BOOLEAN ON Search obj")
            self.is_sota_term = props[0].is_sota_term

        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def store_search_file(self):
        """
        Use search_file_url to download the file 
        and store inside search_file field
        """
        if self.search_file_url:
            t = time.localtime()
            timestamp = time.strftime("%b-%d-%Y_%H%M", t)
            file_name = self.db.name + "-" + timestamp
            uploaded_filename = self.search_file_url.split("/")[-1]
            file_name = file_name + uploaded_filename
            file_temp = NamedTemporaryFile(delete=True)
            file_temp.write(urlopen(self.search_file_url).read())
            file_temp.flush()
            self.search_file.save(file_name , File(file_temp))
            self.save()

class Article(models.Model):
    """
    An Article is just an article. It has no relation to a review.
    """
    title = models.TextField()
    abstract = models.TextField()
    citation = models.TextField(blank=True)
    pubmed_uid = models.TextField(null=True, blank=True)
    pmc_uid = models.TextField(null=True, blank=True)
    article_unique_id = models.CharField(max_length=256, null=True, help_text="A unique id is created to identify identifical articles for the same client across multiple literature reviews")
    full_text = models.FileField(null=True, blank=True,max_length=1000)
    highlighted_full_text = models.FileField(null=True, blank=True,max_length=1000)
    publication_year = models.CharField(null=True, blank=True, max_length=30)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.SET_NULL, null=True)
    journal = models.CharField(max_length=512, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    doi = models.TextField(null=True, blank=True)
    keywords = models.TextField(null=True, blank=True, help_text="article keywords collected from the uploaded file will be a string seperated by ','")
    is_added_to_library = models.BooleanField(
        default=False, null=True, blank=True, 
        help_text="""
        if the article is coming from notebook searches all are hidden by default 
        inside manage citations view, want to show them up? flag this as true
        """
    )
    meta_data = HStoreField(
        null=True,
        blank=True,
        help_text="""
            Storing Extra article fields that may not neccesary exists in all database / file formats
            will try to list below as many fields as I can and from where we're getting them:
            
            Field Name    |   Description                              | File Format (we can extract from) \n
            volume        |   Volume (VL)                              | RIS \n
            volume_number |   issue or number of volumes.(IS)          | RIS \n
            start_page    |   Start Page (SP)                          | RIS \n
            end_page      |   End Page(EP)                             | RIS \n    
            authors       |   AU                                       | All Formats \n      
        """
    )

    def __str__(self):
        return f"{self.title} - {self.literature_review}"

    def save(self, *args, **kwargs):
        from lit_reviews.helpers.articles import create_unique_article_identifier
        
        created = self.pk == None
        if created:
            self.article_unique_id = create_unique_article_identifier(self)

        super().save(*args, **kwargs)

class ArticleReview(models.Model):
    """
    A review is search-specific, since a search pertains to specific device.
    """

    class ArticleReviewState(models.TextChoices):
        UNCLASSIFIED = "U", _("Unclassified")
        INCLUDED = "I", _("Retained")
        MAYBE = "M", _("Maybe")
        EXCLUDED = "E", _("Excluded")
        DUPLICATE = "D", _("Duplicate")

    FULL_TEXT_STATUS_CHOICES = (
        ("uploaded", "uploaded"),
        ("missing", "missing"),
        ("excluded", "excluded"),
    )
    state = models.CharField(
        max_length=1,
        choices=ArticleReviewState.choices,
        default=ArticleReviewState.UNCLASSIFIED,
    )
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="reviews")
    search = models.ForeignKey(LiteratureSearch, on_delete=models.CASCADE)
    exclusion_reason = models.CharField(max_length=2000, null=True, blank=True)
    exclusion_comment = models.TextField(null=True, blank=True, help_text="Extra comment can be added to excluded articles only")
    notes = models.TextField(null=True, blank=True, help_text="general notes attached to the article review")
    processed_abstract = models.TextField(null=True, blank=True)
    processed_title = models.CharField(null=True, blank=True, max_length=5025)
    score = models.IntegerField(default=0, null=True)
    potential_duplicate_for = models.ForeignKey(
        "self", null=True, blank=True, 
        related_name="potential_duplicate_review", 
        on_delete=models.SET_NULL, 
        help_text="Reference to a potential duplicate article review."
    )
    full_text_status = models.CharField(null=True, blank=True, choices=FULL_TEXT_STATUS_CHOICES)

    # AI Values
    ai_state_decision = models.CharField(
        max_length=1,
        choices=ArticleReviewState.choices,
        null=True,
        blank=True,
    )
    ai_exclusion_reason = models.CharField(max_length=2000, null=True, blank=True)
    ai_decision_accepted = models.BooleanField(null=True, blank=True)


    def __str__(self):
        return str(self.article)

    def calculate_full_text_status(self):
        app = ClinicalLiteratureAppraisal.objects.filter(article_review=self).first()
        if self.article.full_text:
            return "uploaded"
        elif (self.state == "E") or (app and app.included == False):
            return "excluded"
        else:
            return "missing"

    @property
    def literature_review_id(self):
        return self.search.literature_review.id

    def get_label(self):
        return self.state.label
    
    def get_absolute_url(self):
        return reverse("lit_reviews:article_review_detail", args=[str(self.search.literature_review.id), str(self.id)])

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        from lit_reviews.tasks import calculate_clinical_appraisal_status_async

        # TODO needs to be handled better, likely pre-save
        old_state = self.state
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )
        new_state = self.state
        if new_state == self.ArticleReviewState.INCLUDED:
            appraisal = ClinicalLiteratureAppraisal.objects.filter(
                article_review=self
            ).first()
            if not appraisal:
                appraisal = ClinicalLiteratureAppraisal.objects.create(
                    article_review=self
                )
                calculate_clinical_appraisal_status_async.delay(appraisal.id)

            else:
                logger.warning(f"Appraisal already exists for Article ID {self.article.id}")
                calculate_clinical_appraisal_status_async.delay(appraisal.id)
                
        elif old_state == self.ArticleReviewState.INCLUDED:
            ClinicalLiteratureAppraisal.objects.filter(article_review=self).delete()
 
    @property
    def article_score(self):
        article_text = str(self.article.abstract).lower()
        keywords = KeyWord.objects.filter(literature_review = self.search.literature_review).first()

        # Here are the point value for each Lit Review
        population_kw_point_value = 2
        intervention_kw_point_value = 3
        comparison_kw_point_value = 3
        outcome_kw_point_value = 4
        exclusion_kw_point_value = -10

        if keywords and article_text:
            pop_list = keywords.population.split(",") if keywords.population else []
            int_list = keywords.intervention.split(",") if keywords.intervention else []
            comp_list = keywords.comparison.split(",") if keywords.comparison else []
            out_list = keywords.outcome.split(",") if keywords.outcome else []
            exc_list = keywords.exclusion.split(",") if keywords.exclusion else []
            score = 0

            for kw in pop_list:
                kw = kw.strip().lower()
                if kw:
                    kw_occ = len(re.findall(r'\b' + re.escape(kw) + r'\b', article_text))
                    score += kw_occ * population_kw_point_value

            for kw in int_list:
                kw = kw.strip().lower()
                if kw:
                    kw_occ = len(re.findall(r'\b' + re.escape(kw) + r'\b', article_text))
                    score += kw_occ * intervention_kw_point_value

            for kw in comp_list:
                logger.debug("kw : " + kw)
                kw = kw.strip().lower()
                if kw:
                    kw_occ = len(re.findall(r'\b' + re.escape(kw) + r'\b', article_text))
                    score += kw_occ * comparison_kw_point_value

            for kw in out_list:
                kw = kw.strip().lower()
                if kw:
                    kw_occ = len(re.findall(r'\b' + re.escape(kw) + r'\b', article_text))
                    score += kw_occ * outcome_kw_point_value

            for kw in exc_list:
                kw = kw.strip().lower()
                if kw:
                    kw_occ = len(re.findall(r'\b' + re.escape(kw) + r'\b', article_text))
                    score += kw_occ * exclusion_kw_point_value

            return score
        else:
            return 0

    @property
    def article_history(self):
        # get old article review for the article and get last_old_article_review
        if self.article.pubmed_uid:
            last_old_article_reviews = ArticleReview.objects.filter(
                article__pubmed_uid=self.article.pubmed_uid
            ).exclude(id = self.id).order_by("-search__created_time")
        elif self.article.pmc_uid:
            last_old_article_reviews = ArticleReview.objects.filter(
                article__pmc_uid=self.article.pmc_uid
            ).exclude(id = self.id).order_by("-search__created_time")
        else:
            last_old_article_reviews = ArticleReview.objects.filter(
                article=self.article
            ).exclude(id = self.id).order_by("-search__created_time")

        return last_old_article_reviews

class FullTextRequest(models.Model):
    article = models.ForeignKey(Article, on_delete=models.DO_NOTHING)

    class FullTextRequestState(models.TextChoices):
        REQUESTED = "Q", _("Requested")
        RECEIVED = "R", _("Received")

    state = models.CharField(
        max_length=1,
        choices=FullTextRequestState.choices,
        default=FullTextRequestState.REQUESTED,
    )


class ClinicalLiteratureAppraisal(models.Model):
    """
    Used for Appendix C (all included articles)
    """

    article_review = models.ForeignKey(
        ArticleReview, on_delete=models.CASCADE, related_name="clin_lit_appr"
    )
    included = models.BooleanField(null=True, blank=True)
    justification = models.TextField(null=True, blank=True)
    app_status = models.CharField(blank=True, null=True, max_length=256)
    is_sota_article = models.BooleanField(null=True, blank=True)
    
    ################################# 01 January 2024 ##############################
    ############### BELOW FIELD ARE NO LONGER USED AND WAS REPLACED BY #############
    ############### AppraisalExtractionField OBJECT FOR EACH FIELD #################
    

    # sota_inclusion_choices = (
    #     ('M', 'Medical Included'), #SOTA: Establishment of current knowledge/ the state of the art on the medical condition.
    #     ('T','Therapies and Treatments'), #SOTA: Establishment of current knowledge/ the state of the art on alternative therapies/treatments.
    #     ('R', 'Risk/Benefit'), # SOTA: Determination and justification of criteria for the evaluation of the risk/benefit relationship.
    #     ('S', 'Side Effects'), #SOTA: Determination and justification of criteria for the evaluation of acceptability of undesirable side-effects.
    #     ('EQ', 'Equivalence'), #SOTA: Determination of equivalence
    #     ('E', 'Excluded'),
    # )
    # sota_inclusion = models.CharField(
    #     max_length=2, choices=sota_inclusion_choices, null=True,  blank=True
    # )

    sota_exclusion_choices = (
        (
            "NC",
            "Describes technical or non-clinical study results only, including animal or cadaver studies",
        ),
        ("OP", "Contains unsubstantiated opinions"),
        ("KN", "Do not represent the current knowledge/state of the art"),
        ("AG", "The articles are not in line with the established time frame"),
        ("EN", "Non-English Language"),
        (
            "PU",
            "Publications types other than Peer reviewed guidelines, International peer reviewed consensus statements, State of the Art review (can be narrative review), systematic review, or Meta-Analysis",
        ),
    )
    sota_exclusion_reason = models.CharField(
        max_length=200, choices=sota_exclusion_choices,blank=True, null=True
    )

    sota_suitability_choices = (
        ("CK0", "CK0: No SoTA Information"),
        (
            "CK1",
            "CK1: Establishment of current knowledge/ the state of the art on the medical condition",
        ),
        (
            "CK2",
            "CK2: Establishment of current knowledge/ the state of the art on alternative therapies/treatments",
        ),
        (
            "CK3",
            "CK3: Determination and justification of criteria for the evaluation of the risk/benefit relationship",
        ),
        (
            "CK4",
            "CK4: Determination and justification of criteria for the evaluation of acceptability of undesirable side-effects",
        ),
        ("CK5", "CK5: Determination of equivalence"),
        ("CK6", "CK6: Justification of the validity of surrogate endpoints"),
    )
    sota_suitability = models.CharField(
        max_length=3, choices=sota_suitability_choices, blank=True, null=True
    )

    class AppropriateDeviceChoices(models.TextChoices):
        ACTUAL_DEVICE = "D1", _("Actual Device")
        SIMILAR_DEVICE = "D2", _("Similar Device")
        OTHER_DEVICE = "D3", _("Other Device")

    appropriate_device = models.CharField(
        max_length=2, choices=AppropriateDeviceChoices.choices, null=True, blank=True
    )

    class AppropriateApplicationChoices(models.TextChoices):
        ACTUAL_DEVICE = "A1", _("Same Use")
        SIMILAR_DEVICE = "A2", _("Minor Deviation")
        OTHER_DEVICE = "A3", _("Major Deviation")

    appropriate_application = models.CharField(
        max_length=2,
        choices=AppropriateApplicationChoices.choices,
        null=True,
        blank=True,
    )

    class MDCGRankingChoices(models.TextChoices):
        RANK_O1 = "Rank 01", _("Rank 01")
        RANK_O2 = "Rank 02", _("Rank 02")
        RANK_O3 = "Rank 03", _("Rank 03")
        RANK_O4 = "Rank 04", _("Rank 04")
        RANK_O5 = "Rank 05", _("Rank 05")
        RANK_O6 = "Rank 06", _("Rank 06")
        RANK_O7 = "Rank 07", _("Rank 07")
        RANK_O8 = "Rank 08", _("Rank 08")
        RANK_O9 = "Rank 09", _("Rank 09")
        RANK_10 = "Rank 10", _("Rank 10")
        RANK_11 = "Rank 11", _("Rank 11")
        RANK_12 = "Rank 12", _("Rank 12")

    mdcg_ranking = models.CharField(
        max_length=126,
        choices=MDCGRankingChoices.choices,
        null=True,
        blank=True,
    )

    class AppropriatePatientGroupChoices(models.TextChoices):
        APPLICABLE = "P1", _("Applicable")
        LIMITED = "P2", _("Limited")
        DIFFERENT_POPULATION = "P3", _("Different Population")

    appropriate_patient_group = models.CharField(
        max_length=2,
        choices=AppropriatePatientGroupChoices.choices,
        null=True,
        blank=True,
    )

    class AcceptableCollationChoices(models.TextChoices):
        HIGH_QUALITY = "R1", _("High Quality")
        MINOR_DEFICIENCIES = "R2", _("Minor Deficiencies")
        INSUFFICIENT_INFORMATION = "R3", _("Insufficient Information")

    acceptable_collation_choices = models.CharField(
        max_length=2, choices=AcceptableCollationChoices.choices, null=True, blank=True
    )

    class DataContributionChoices(models.TextChoices):
        EXPERT = "E", _("Yes (Expert Opinion)")
        REVIEW = "R", _("Yes (Review Article)")
        QUESTION = "Q", _("Yes (Questionnaire)")
        YES = "Y", _("Yes")
        NO = "N", _("No")

    data_contribution = models.CharField(
        max_length=1, choices=DataContributionChoices.choices, null=True, blank=True
    )

    grade_primary_choices = (
        ("VERY LOW", "Very Low"),
        ("LOW", "Low"),
        ("MODERATE", "Moderate"),
        ("HIGH", "High"),
        ("VERY HIGH", "Very High"),
    )

    grade_primary = models.CharField(
        max_length=20, choices=grade_primary_choices, null=True, blank=True
    )

    grade_likely_choices = (
        ("LIKELY", "Likely"),
        ("VERY LIKELY", "Very Likely"),
    )

    grade_serious_choices = (("SERIOUS", "Serious"), ("VERY SERIOUS", "Very Serious"))
    grade_risk_bias = models.CharField(
        max_length=20, choices=grade_likely_choices, null=True, blank=True
    )
    grade_imprecision = models.CharField(
        max_length=20, choices=grade_serious_choices, null=True, blank=True
    )
    grade_rct_incon = models.CharField(
        max_length=20, choices=grade_serious_choices, null=True, blank=True
    )
    grade_indir = models.CharField(
        max_length=20, choices=grade_serious_choices, null=True, blank=True
    )
    grade_rct_limit = models.CharField(
        max_length=20, choices=grade_serious_choices, null=True, blank=True
    )

    #### appraisal questions yes/nos
    yes_no = (
        ("YES", "Yes"),
        ("NO", "No"),
    )
    design_yn = models.CharField(max_length=20, choices=yes_no, null=True, blank=True)
    outcomes_yn = models.CharField(max_length=20, choices=yes_no, null=True, blank=True)
    followup_yn = models.CharField(max_length=20, choices=yes_no, null=True, blank=True)
    stats_yn = models.CharField(max_length=20, choices=yes_no, null=True, blank=True)
    study_size_yn = models.CharField(
        max_length=20, choices=yes_no, null=True, blank=True
    )
    clin_sig_yn = models.CharField(max_length=20, choices=yes_no, null=True, blank=True)
    clear_conc_yn = models.CharField(
        max_length=20, choices=yes_no, null=True, blank=True
    )
    ## data extraction fields
    safety_short = models.CharField(max_length=25, null=True, blank=True)
    safety = models.TextField(null=True, blank=True)

    performance_short = models.CharField(max_length=25, null=True, blank=True)
    performance = models.TextField(null=True, blank=True)

    adverse_events_short = models.CharField(max_length=25, null=True, blank=True)
    adverse_events = models.TextField(null=True, blank=True)

    sota_short = models.CharField(max_length=25, null=True, blank=True)
    sota = models.TextField(null=True, blank=True)

    guidance_short = models.CharField(max_length=25, null=True, blank=True)
    guidance = models.TextField(null=True, blank=True)

    other_short = models.CharField(max_length=25, null=True, blank=True)
    other = models.TextField(null=True, blank=True)

    study_design_short = models.CharField(max_length=25, null=True, blank=True)
    study_design = models.TextField(null=True, blank=True)

    total_sample_size_short = models.CharField(max_length=25, null=True, blank=True)
    total_sample_size = models.TextField(null=True, blank=True)

    objective_short = models.CharField(max_length=25, null=True, blank=True)
    objective = models.TextField(null=True, blank=True)

    device_name = models.CharField(max_length=200, null=True, blank=True)
    indication = models.CharField(max_length=200, null=True, blank=True)

    treatment_modality_short = models.CharField(max_length=25, null=True, blank=True)
    treatment_modality = models.TextField(null=True, blank=True)

    study_conclusions_short = models.CharField(max_length=25, null=True, blank=True)
    study_conclusions = models.TextField(null=True, blank=True)
    ##### end data extraction fields.

    ###################### END OF NOT USED FIELDS ###########################

    ## outcomes fields.
    ##### these below fields are not being used as of 06-28-22 ##########
    outcome_measures = models.BooleanField(null=True, blank=True)
    appropriate_followup = models.BooleanField(null=True, blank=True)
    statistical_significance = models.BooleanField(null=True, blank=True)
    clinical_significance = models.BooleanField(null=True, blank=True)
    ###################### END of not used fields ########################

    # AI Processing Status
    AI_GENERATION_STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    ai_generation_status = models.CharField(
        max_length=20,
        choices=AI_GENERATION_STATUS_CHOICES,
        default='not_started',
        help_text="Current status of AI extraction field generation for this appraisal"
    )
    
    ai_last_processed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when AI last processed this appraisal"
    )

    def __str__(self):
        return f"Appraisal: {self.article_review}"

    def get_absolute_url(self):
        return reverse("lit_reviews:clinical_literature_appraisal", args=[str(self.literature_review_id), str(self.id)])

    @property
    def literature_review_id(self):
        return self.article_review.literature_review_id
    
    @property
    def is_ck3(self):
        extraction = ExtractionField.objects.filter(literature_review__id=self.literature_review_id, name="sota_suitability").first()
        if extraction:
            app_extraction = AppraisalExtractionField.objects.filter(extraction_field=extraction, clinical_appraisal=self).first()
            if app_extraction:
                if app_extraction.value and "CK3" in app_extraction.value:
                    return True
        
        return False

    @property
    def status(self):
        # if object is created already
        if self.pk:
            app_status = ""
            app = self
            
            app_article =  app.article_review.article
            full_text_is_not_uploaded = ( app_article.full_text in [""] or not app_article.full_text ) and app.included != False
            
            ## not started
            not_started = app.included is None or app.is_sota_article is None
            
            from lit_reviews.helpers.articles import check_extraction_section_completion, get_or_create_appraisal_extraction_fields
            ### need to decide if we want to enforce all of these (maybe not 100% necessary)
            if app.included:
                # suit_outcomes = (
                #     app.appropriate_device is None
                #     or app.appropriate_application is None
                #     or app.appropriate_patient_group is None
                #     or app.data_contribution is None
                #     # or app.outcome_measures is None
                #     # or app.appropriate_followup is None
                #     # or app.statistical_significance is None
                #     # or app.clinical_significance is None
                #     or app.acceptable_collation_choices is None
                # )
                suit_outcomes = check_extraction_section_completion(app, "SO")

            else:
                suit_outcomes = False

            needs_exclusion = (app.included is False and app.is_sota_article is False) and (
                app.justification is None or app.justification == ""
            )

            ## sota not completed
            # sota = app.is_sota_article and (app.sota_suitability is None or (not app.included and not app.sota_exclusion_reason))
            review = app.article_review.search.literature_review
            suitability_extraction = ExtractionField.objects.filter(name="sota_suitability", literature_review=review).first()
            if suitability_extraction:
                app_suitability_extraction = get_or_create_appraisal_extraction_fields(app, suitability_extraction)
                sota_suitability = app_suitability_extraction.value 
            exclusion_reason_extraction = ExtractionField.objects.filter(name="sota_exclusion_reason", literature_review=review).first()
            if exclusion_reason_extraction:
                app_sota_exclusion_reason_extraction = get_or_create_appraisal_extraction_fields(app, exclusion_reason_extraction)
                sota_exclusion_reason = app_sota_exclusion_reason_extraction.value 
            if suitability_extraction and exclusion_reason_extraction:
                sota = app.is_sota_article and (
                    not sota_suitability 
                    or (not app.included and not sota_exclusion_reason) 
                )
            else:
                sota = app.is_sota_article and check_extraction_section_completion(app, "ST")

            extraction_fields_incomplete = check_extraction_section_completion(app, "EF")

            ## device review not completed
            device = (app.is_sota_article is False and app.included) and (
                # app.design_yn is None
                # or app.outcomes_yn is None
                # or app.followup_yn is None
                # or app.stats_yn is None
                # # or app.study_size_yn is None
                # or app.clin_sig_yn is None
                # # or app.clear_conc_yn is None
                # or app.appropriate_device is None
                # or app.appropriate_application is None
                # or app.appropriate_patient_group is None
                # or app.data_contribution is None
                # # or app.grade_primary is None
                check_extraction_section_completion(app, "QC") or check_extraction_section_completion(app, "SO")
            )

            if full_text_is_not_uploaded:
                app_status = "Missing full text pdf/Incomplete"

            elif not_started:
                app_status = "Full text uploaded/Ready for Review"

            elif suit_outcomes:
                app_status = "Needs Suitability/Outcomes Dropdowns"

            elif sota:
                app_status = "Incomplete Sota"

            elif device:
                app_status = "Incomplete Device Review"

            elif needs_exclusion:
                app_status = "Missing Excl. Justification"
        
            elif extraction_fields_incomplete and (app.is_sota_article is False and app.included):
                app_status = "Incomplete Extraction Fields"

            else:
                app_status = "Complete"

            return app_status


class FinalReportConfig(models.Model):
    YES_NO_CHOICE = ((True, 'Yes'), (False, 'No'))
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)

### dropdowns 

    sota_suitability = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    appropriate_device= models.BooleanField(default=True, choices=YES_NO_CHOICE)
    appropriate_application= models.BooleanField(default=True, choices=YES_NO_CHOICE)
    appropriate_patient_group= models.BooleanField(default=True, choices=YES_NO_CHOICE)
    acceptable_collation_choices= models.BooleanField(default=True, choices=YES_NO_CHOICE)
    data_contribution= models.BooleanField(default=True, choices=YES_NO_CHOICE)

    ## grades if primary, include all. 
    grade = models.BooleanField(default=True, choices=YES_NO_CHOICE)

    ## yes no questions
    design_yn = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    outcomes_yn = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    followup_yn  = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    stats_yn = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    study_size_yn = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    clin_sig_yn = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    clear_conc_yn = models.BooleanField(default=True, choices=YES_NO_CHOICE)
    
    ## long forms extraction fields.
    safety = models.BooleanField(default=True)
    performance = models.BooleanField(default=True)
    adverse_events = models.BooleanField(default=True)
    sota = models.BooleanField(default=True)
    guidance = models.BooleanField(default=True)
    other = models.BooleanField(default=True)
    study_design = models.BooleanField(default=True)
    total_sample_size = models.BooleanField(default=True)
    objective = models.BooleanField(default=True)
    treatment_modality = models.BooleanField(default=True)
    study_conclusions = models.BooleanField(default=True)



    ## outcomes fields
    data_contribution= models.BooleanField(default=True)
    outcome_measures = models.BooleanField(default=True)
    appropriate_followup = models.BooleanField(default=True)
    statistical_significance = models.BooleanField(default=True)
    clinical_significance = models.BooleanField(default=True)
    

    #writeup
    justification = models.BooleanField(default=True)




class AdverseEventRegulatoryBody(models.Model):
    name = models.TextField(unique=True)


class AdverseEventProductCodes(models.Model):
    # TODO one time fill from FDA
    source = models.ForeignKey(AdverseEventRegulatoryBody, on_delete=models.CASCADE)
    code = models.CharField(max_length=150)
    description = models.TextField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "code"],
                name="unique_source_code",
            )
        ]


# class AdverseRecallSearch(models.Model):
#     """
#     Many AdverseEventSearches per LiteratureReview
#     """

#     time_performed = models.DateTimeField(auto_now=True)
#     literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
#     db = models.ForeignKey(
#         NCBIDatabase, on_delete=models.CASCADE, null=True, blank=True
#     )
#     product_code = models.ForeignKey(AdverseEventProductCodes, on_delete=models.CASCADE)
#     recalls = models.ManyToManyField(AdverseRecall, related_name="ae_recalls")


# class AdverseEventSearch(models.Model):
#     """
#     Many AdverseEventSearches per LiteratureReview
#     """

#     time_performed = models.DateTimeField(auto_now=True)
#     literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
#     db = models.ForeignKey(
#         NCBIDatabase, on_delete=models.CASCADE, null=True, blank=True
#     )
#     product_code = models.ForeignKey(AdverseEventProductCodes, on_delete=models.CASCADE)
#     events = models.ManyToManyField(AdverseEvent, related_name="ae_events")
#     ## bad related name, should be ae_search instead.


class AdverseRecallReview(models.Model):
    ae = models.ForeignKey(
        AdverseRecall,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ae_recalls_reviews",
    )
    search = models.ForeignKey(
        LiteratureSearch, on_delete=models.CASCADE, null=True, blank=True
    )

    class FeedbackChoices(models.TextChoices):
        INCLUDED = "IN", _("Included")
        SIMILAR = "SM", _("Similar")
        EXCLUDED = "EX", _("Excluded or not Relevant")
        UNREVIEWED = "UN", _("Not Reviewed")
        DUPLICATE = "DU", _("Duplicate")

    state = models.CharField(
        max_length=2,
        choices=FeedbackChoices.choices,
        default=FeedbackChoices.UNREVIEWED,
    )

    @property
    def literature_review_id(self):
        return self.search.literature_review.id


class AdverseEventReview(models.Model):
    ae = models.ForeignKey(
        AdverseEvent,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ae_reviews",
    )
    search = models.ForeignKey(
        LiteratureSearch, on_delete=models.CASCADE, null=True, blank=True
    )

    class FeedbackChoices(models.TextChoices):
        INCLUDED = "IN", _("Included")
        SIMILAR = "SM", _("Similar")
        EXCLUDED = "EX", _("Excluded or not Relevant")
        UNREVIEWED = "UN", _("Not Reviewed")
        DUPLICATE = "DU", _("Duplicate")

    state = models.CharField(
        max_length=2,
        choices=FeedbackChoices.choices,
        default=FeedbackChoices.UNREVIEWED,
    )

    is_duplicate = models.BooleanField(default=False, null=True, blank=True)


    @property
    def literature_review_id(self):
        return self.search.literature_review.id


def unique_file_name(instance, filename):
    # if the filename already exists inside aws s3 bucket update it with uuid 
    # so it doesn't override the existing one
    storage = default_storage

    # Check if the file exists and rename it
    if storage.exists(filename):
        unique_id = uuid.uuid4()
        filefolders = filename.split("/")
        filefolders.insert(len(filefolders)-1, str(unique_id)) 
        filename = "/".join(filefolders) 
    
    logger.info(filename)
    return filename


class FinallReportJob(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    version_number = models.DecimalField(max_digits=3, decimal_places=1, default="1.0", null=True, blank=True)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)

    type_choices = (
        ("PROTOCOL", "PROTOCOL"),
        ("REPORT", "REPORT"),
        ("ABBOTT_REPORT", "ABBOTT_REPORT"),
        ("CONDENSED_REPORT", "CONDENSED_REPORT"),
        ("SECONDPASS", "SECONDPASS"),
        ("APPENDIX_E2", "APPENDIX_E2"),
        ("ARTICLE_REVIEWS", "ARTICLE_REVIEWS"),
        ("ARTICLE_REVIEWS_RIS", "ARTICLE_REVIEWS_RIS"),
        ("PRISMA", "PRISMA"),
        ("SECOND_PASS_WORD", "SECOND_PASS_WORD"),
        ("SECOND_PASS_RIS", "SECOND_PASS_RIS"),
        ("FULL_TEXT_ZIP", "FULL_TEXT_ZIP"),
        ("TERMS_SUMMARY", "TERMS_SUMMARY"),
        ("SEARCH_VALIDATION_ZIP", "SEARCH_VALIDATION_ZIP"),
        ("DUPLICATES", "DUPLICATES"),
        ("AUDIT_TRACKING_LOGS", "AUDIT_TRACKING_LOGS"),
        ("DEVICE_HISTORY", "DEVICE_HISTORY"),
        ("CUMULATIVE_REPORT", "CUMULATIVE_REPORT"),
    )
    report_type = models.CharField(max_length=30, choices=type_choices, default="REPORT")

    status_choices = (
        ("COMPLETE", "COMPLETE"),
        ("INCOMPLETE-ERROR", "INCOMPLETE-ERROR"),
        ("NOT RUN", "NOT RUN"),
        ("RUNNING", "RUNNING"),
    )
    status = models.CharField(max_length=30, choices=status_choices, default="NOT RUN")

    generte_zip_status = models.CharField(max_length=30, choices=status_choices, default="NOT RUN")
    error_msg = models.TextField(blank=True, null=True)
    generate_zip_error = models.TextField(blank=True, null=True)

   # protocol = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    report = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    prisma = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    condensed_report = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    appendix_e2 = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    terms_summary_report = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    vigilance_report = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    protocol = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    second_pass_articles = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    second_pass_word = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    second_pass_ris = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    article_reviews_ris = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    verification_zip = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    duplicates_report = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    fulltext_zip = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    audit_tracking_logs = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    missing_clinical_appraisals = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    all_articles_review = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    device_history_zip = models.FileField(null=True, blank=True, upload_to=unique_file_name)
    cumulative_report = models.FileField(null=True, blank=True, upload_to=unique_file_name)

    # extra custom client reports 
    abbot_report = models.FileField(null=True, blank=True, upload_to=unique_file_name)

    comment = models.TextField(null=True, blank=True)
    is_simple = models.BooleanField(default=False)
    job_started_time = models.DateTimeField(null=True, default=None)

    ######### NO LONGER USED FIELDS ###################
    appendix_a = models.FileField(null=True, blank=True)
    appendix_b_all = models.FileField(null=True, blank=True)
    appendix_b_retinc = models.FileField(null=True, blank=True)
    appendix_c_all = models.FileField(null=True, blank=True)
    appendix_c_retinc = models.FileField(null=True, blank=True)
    appendix_d = models.FileField(null=True, blank=True)
    appendix_e = models.FileField(null=True, blank=True)
    prisma = models.FileField(null=True, blank=True)
    ######### NO LONGER USED FIELDS ###################

    @property
    def escaped_error_msg(self):
        if self.error_msg:
            return json.dumps(self.error_msg)
        else:
            return None

    @property
    def escaped_generate_zip_error(self):
        if self.generate_zip_error:
            return json.dumps(self.generate_zip_error)
        else:
            return None

################## Old Model we are no longer using this #############
class AdverseDatabaseSummary(models.Model):
    database = models.ForeignKey(NCBIDatabase, on_delete=models.DO_NOTHING)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.DO_NOTHING)
    summary = models.TextField()
######################################################################

class AdversDatabaseSummary(models.Model):
    database = models.ForeignKey(NCBIDatabase, on_delete=models.CASCADE)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    summary = models.TextField()

class SearchTermsPropsSummaryReport(models.Model):
    status_choices = (
        ("COMPLETE", "COMPLETE"),
        ("RUNNING", "RUNNING"),
        ("NOT RUN", "NOT RUN"),
        ("INCOMPLETE-ERROR", "INCOMPLETE-ERROR"),
    )

    timestamp = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(null=True, default=None)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    status = models.CharField(max_length=30, choices=status_choices, default="NOT RUN")
    doc = models.FileField(null=True, blank=True)

    def __str__(self):
        return f"{self.literature_review.device} - {self.literature_review.client} - {self.id}"

class SearchTermValidator(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    status_choices = (
        ("COMPLETE", "COMPLETE"),
        ("INCOMPLETE-ERROR", "INCOMPLETE-ERROR"),
        ("NOT RUN", "NOT RUN"),
        ("RUNNING", "RUNNING"),
    )
    status = models.CharField(max_length=30, choices=status_choices, default="NOT RUN")
    error_msg = models.CharField(max_length=10024)

class DataBaseDump(models.Model):
    timestamp = models.DateTimeField(auto_now=True)
    file = models.FileField(upload_to="db_dumps")


class ExtractionField(models.Model):
    """
    This extraction field serve as a template
    appraisals extraction field values are stored inside AppraisalExtractionField
    """
    TYPE_CHOICES = (
        ("TEXT", "Text"),
        ("LONG_TEXT", "Long Text"),
        ("DROP_DOWN", "Drop Down"),
    )
    CATEGORIES = (
        ("ST", "Study Design"),
        ("T", "Treatment"),
        ("SR", "Study Result"),
    )
    SECTIONS = (
        ("SO", "Suitability and Outcomes (All Articles including SoTA)"),
        ("QC", "Quality and Contribution Questions"),
        ("MR", "MDCG Ranking"),
        ("EF", "Extraction Fields"),
        ("ST", "SoTa"),
        ("CS", "Custom Section"),
    )

    name = models.CharField(max_length=512)
    ai_prompte = models.TextField(help_text="AI Prompte ll help generate and use ai models", max_length=512, null=True, blank=True)
    type = models.CharField(max_length=512, choices=TYPE_CHOICES)
    drop_down_values = models.TextField(null=True) 
    is_template = models.BooleanField(default=False)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE, related_name="extraction_fields")
    category = models.CharField(max_length=10, choices=CATEGORIES, default="ST")
    field_section = models.CharField(max_length=10, choices=SECTIONS, default="EF")
    description = models.TextField(help_text="A descriptive label that will be shown in the form", null=True, blank=True)
    name_in_report = models.CharField(max_length=512, null=True, blank=True)
    field_order = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        # if no name_in_report provided, take the name
        if not self.name_in_report:
            self.name_in_report = self.name

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('name', 'literature_review',)

    def __str__(self):
        return f"{self.name} - {self.literature_review}" 
                  
    
class AppraisalExtractionField(models.Model):
    AI_STATUS_CHOICES = (
        ('accepted', 'Accepted'),
        ('edited', 'Edited'),
        ('rejected', 'Rejected'),
        ('not_reviewed', 'Not Reviewed')
    )
    extraction_field = models.ForeignKey(ExtractionField, on_delete=models.CASCADE, related_name="apprailsal_extraction_fields")
    clinical_appraisal = models.ForeignKey(ClinicalLiteratureAppraisal, on_delete=models.CASCADE,  related_name="fields")
    value = models.TextField(null=True)
    extraction_field_number = models.SmallIntegerField(
        default=1,
        help_text="Each Appraisal Field can have multiple values (Sub Extractions), we can differentiate between the different values by their number the default value has number 1"
    )
    ai_value = models.CharField(
        max_length=2048, 
        null=True, 
        blank=True,
        help_text="AI generated value for this extraction field"
    )
    ai_simplified_value = models.CharField(
        max_length=1024, 
        null=True, 
        blank=True,
        help_text="AI simplified generated value for this extraction field"
    )
    ai_value_status = models.CharField(
        max_length=12,
        choices=AI_STATUS_CHOICES,
        default='not_reviewed',
        help_text="Status of the AI generated value - whether it was accepted, edited, rejected, or not reviewed"
    )

    def __str__(self):
        article__title = self.clinical_appraisal.article_review.article.title
        return f"{self.extraction_field.name} - {article__title}"

class SearchConfiguration(models.Model):
    CONFIG_TYPE_CHOICES = [
        ('recommended', 'Recommended'),
        ('manual', 'Manual'),
    ]
    database = models.ForeignKey(NCBIDatabase, on_delete=models.CASCADE)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE, null=True, blank=True, related_name="search_configurations")
    config_type = models.CharField(
        max_length=20,
        choices=CONFIG_TYPE_CHOICES,
        default='recommended',
        help_text="Indicates whether the configuration is recommended or manual."
    )
    is_template = models.BooleanField(default=False, help_text="""
        Template search configuration is just a placeholder for the strandard configurations that will be included in every new projuct
    """)

    def __str__(self):
        return f"{self.database} Configuration {self.literature_review if self.literature_review else 'Template'}"


class SearchParameter(models.Model):
    TYPES = (
        ("NB", "NUMBER"),
        ("TX", "Text"),
        ("DP", "Drop Down"),
        ("CK", "Check Box"),
        ("DT", "Date"),
    )
    name = models.CharField(max_length=512)
    search_config = models.ForeignKey(SearchConfiguration, on_delete=models.CASCADE, related_name="params")
    type = models.CharField(max_length=512, choices=TYPES)
    options = models.TextField(null=True)
    value = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.search_config}"

    def save(self, *args, **kwargs):
        super(SearchParameter, self).save(*args, **kwargs)
        if self.search_config.is_template:
            reviews = LiteratureReview.objects.all()
            for review in reviews:
                review_param_query = SearchParameter.objects.filter(
                    search_config__database=self.search_config.database,
                    search_config__literature_review=review, 
                    search_config__is_template=False, 
                    name=self.name
                )
                if review_param_query.exists():
                    review_param = review_param_query.first()
                    review_param.name = self.name
                    review_param.type = self.type
                    review_param.options = self.options
                    review_param.save()
                    logger.info(f"Configuration parameters has been updated for {review}.")

                else:
                    search_config = SearchConfiguration.objects.get_or_create(
                        database=self.search_config.database,
                        literature_review=review
                    )[0]
                    review_param = SearchParameter.objects.create(
                        name=self.name,
                        search_config=search_config,
                        type=self.type,
                        options=self.options,
                    )
                    logger.info(f"Configuration parameters created for {review}.")


class ScraperReport(models.Model):
    STATUS_CHOICES = (
        ("SUCCESS", "SUCCESS"),
        ("FAILED", "FAILED"),
        ("EXCLUDED", "EXCLUDED"),
    )

    start_date = models.DateField()
    end_date = models.DateField()
    applied_filters = models.TextField(null=True)
    search = models.ForeignKey(LiteratureSearch, on_delete=models.SET_NULL, null=True)
    search_term = models.TextField()
    database_name = models.CharField(max_length=126)
    script_timestamp = models.DateTimeField(default=timezone.now) 
    status = models.CharField(max_length=52, choices=STATUS_CHOICES)
    results_file = models.URLField(null=True)
    result_count = models.IntegerField(null=True)
    errors = models.TextField()
    warnings = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.SET_NULL, null=True)
    failure_stage_screenshot = models.ImageField(null=True)
    
    def __str__(self):
        return f"{self.literature_review}-{self.database_name}-{self.search_term}"


class SearchTermPreview(models.Model):
    STATUS_CHOICES = (
        ("NOT RUN", "NOT RUN"),
        ("RUNNING", "RUNNING"),
        ("COMPLETED", "COMPLETED"),
        ("FAILED", "FAILED"),
    )

    status = models.CharField(choices=STATUS_CHOICES, max_length=32, default="NOT RUN")
    errors = models.TextField(null=True)
    literature_search = models.ForeignKey(LiteratureSearch, on_delete=models.CASCADE)
    results_url = models.CharField(max_length=1112, null=True, help_text="some search database results can be accessed through a URL generated from the database directly")
    results = models.TextField(null=True, help_text="results is a strigified json file for all found articles")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

class ArticlePreview(models.Model):
    title = models.CharField(max_length=512)
    abstract = models.TextField(null=True) 
    citation = models.TextField(null=True)
    preview = models.ForeignKey(SearchTermPreview, models.CASCADE, related_name="preview_articles")


class ArticleTag(models.Model):
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=112)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=64, default="#ffffff")
    article_reviews = models.ManyToManyField(ArticleReview, related_name="tags")
    articles = models.ManyToManyField(Article, related_name="tags")

    def __str__(self):
        return self.name

    def hex_to_rgba(self):
        # get the rbga equivlant to article tag color with 50% opacity
        # Remove '#' if present and convert hex to RGB
        hex_color = self.color.lstrip('#')
        rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Convert RGB to RGBA with 50% opacity
        rgba_color = rgb_color + (0.2,)
        return rgba_color


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    article_review = models.ForeignKey(
        ArticleReview, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class CustomerSettings(models.Model):
    """ 
    Each Customer (Client / Company) can set a default settings for his literature reviews / projects
    these configs includes the file exported formats for RIS files, default extraction fields for his projects ...etc  
    """
    FULL_TEXT_FORMAT_CHOICES = (
        ("A", "Authors - Year Of Publication - First Pieces of the Title"),
        ("B", "First Pieces of the Title - Authors - Year Of Publication"),
        ("C", "Year Of Publication - Authors - First Pieces of the Title"),
    )

    ris_file_fields = models.CharField(max_length=1024, default=json.dumps(RIS_FILE_FIELDS))
    client = models.ForeignKey(Client, null=True, on_delete=models.CASCADE)

    ################# RIS Fields per to Article Fields ##############
    ris_article_title = models.CharField(max_length=12, default="TI")
    ris_article_abstract = models.CharField(max_length=12, default="AB")
    ris_article_search_term_index = models.CharField(max_length=12, default="RN")
    ris_article_state = models.CharField(max_length=12, default="LB")
    ris_article_notes = models.CharField(max_length=12, default="N1")
    ris_article_doi = models.CharField(max_length=12, default="DO")
    ris_article_keywords = models.CharField(max_length=12, default="KW")
    ris_article_publication_year = models.CharField(max_length=12, default="PY")
    ris_article_journal_name = models.CharField(max_length=12, default="JO")
    ris_article_urls = models.CharField(max_length=12, default="UR")
    ris_articles_authors = models.CharField(max_length=12, default="AU")
    ##################################################################

    full_texts_naming_format = models.CharField(max_length=112, choices=FULL_TEXT_FORMAT_CHOICES, default="A")
    
    # AI Extraction Settings
    automatic_ai_extraction = models.BooleanField(
        default=False,
        help_text="Automatically extract study information from the Full Text PDF when it's uploaded"
    )


class DuplicationReport(models.Model):
    STATUS_CHOICES = (
        ("RUNNING", "RUNNING"),
        ("COMPLETED", "COMPLETED"),
        ("FAILED", "FAILED"),
    )
    timestamp = models.DateTimeField(auto_now=True)
    literature_review = models.ForeignKey(LiteratureReview, on_delete=models.CASCADE)
    status = models.CharField(max_length=52, choices=STATUS_CHOICES, default="COMPLETED")
    duplicates_count = models.IntegerField(null=True, default=0)
    needs_update = models.BooleanField(default=True, help_text="whithin a project whenever a new article is imported this should be updated to true")

    def __str__(self):
        return f"Duplication Report for {self.literature_review}"
    
    def save(self, *args, **kwargs):
        # Optionally, you can update the timestamp manually here if needed
        self.timestamp = timezone.now()
        super(DuplicationReport, self).save(*args, **kwargs)


class SearchLabelOption(models.Model):
    label = models.TextField() 
    customer_settings = models.ForeignKey(
        CustomerSettings,
        on_delete=models.CASCADE,
        related_name='search_label_options'
    )

    def __str__(self):
        return self.label

class DuplicatesGroup(models.Model):
    original_article_review = models.ForeignKey(ArticleReview, on_delete=models.CASCADE)
    duplicates = models.ManyToManyField(ArticleReview, related_name="duplicates_articles")

    def __str__(self):
        return f"Duplication Articles for {self.original_article_review}"
        

class LivingReview(models.Model):
    interval_choices = (
        ("weekly", "weekly"),
        ("monthly", "monthly"),
        ("quarterly", "quarterly"),
        ("annually", "annually"),
    )
    alert_choices = (
        ("under_evaluation", "Under Evaluation Only"),
        ("competitor", "Competitor Only"),
        ("similar", "Similar Only"),
        ("all", "All Devices (Under, Competitor and Similar)"),
    )

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="under_evaluation_livings")
    similar_devices = models.ManyToManyField(Device, related_name="similar_livings", null=True, blank=True)
    competitor_devices = models.ManyToManyField(Device, related_name="competitor_livings", null=True, blank=True)
    interval = models.CharField(max_length=32, choices=interval_choices, default="weekly")  
    start_date = models.DateField()
    project_protocol = models.ForeignKey(LiteratureReview, on_delete=models.SET_NULL, null=True, blank=True, help_text="copy protocol data and search terms from this project in the first run")
    alert_type = models.CharField(max_length=32, choices=alert_choices, null=True, blank=True, help_text="Send alerts when device is found in articles") 
    is_active = models.BooleanField(default=True, help_text="Active reviews runs and create new projects on a regular bases in accordance with the selected interval")

    def __str__(self):
        return f"{str(self.device)} {str(self.start_date)}"

    def does_user_have_access(self, user):
        if user.is_superuser:
            return True
        else:
            return self.project_protocol.client in user.my_companies
        

class SupportRequestTicket(models.Model):
    FOLLOW_UP_CHOICES = (
        ("phone", "Phone"),
        ("email", "Email"),
        ("teams", "Teams Meeting"),
    )
    
    STATUS_CHOICES = (
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("waiting_for_response", "Waiting for Response"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_tickets")
    description = models.TextField(help_text="Detailed description of the issue or request")
    demo_video = models.URLField(
        null=True, 
        blank=True,
        help_text="URL link to a demo video showing the issue (Loom)"
    )
    follow_up_option = models.CharField(
        max_length=20, 
        choices=FOLLOW_UP_CHOICES, 
        default="email",
        help_text="Preferred method for follow-up communication"
    )
    ticket_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="open",
        help_text="Current status of the support ticket"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    solved_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date when the ticket was resolved"
    )
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = "Support Request Ticket"
        verbose_name_plural = "Support Request Tickets"
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.user.username} - {self.ticket_status}"
    
    def save(self, *args, **kwargs):
        # Automatically set solved_date when status changes to resolved or closed
        if self.ticket_status in ['resolved', 'closed'] and not self.solved_date:
            self.solved_date = timezone.now()
        # Clear solved_date if ticket is reopened
        elif self.ticket_status not in ['resolved', 'closed'] and self.solved_date:
            self.solved_date = None
        
        super().save(*args, **kwargs)
    
    @property
    def is_open(self):
        return self.ticket_status in ['open', 'in_progress', 'waiting_for_response']
    
    @property
    def days_since_created(self):
        return (timezone.now() - self.created_date).days
    
    @property
    def resolution_time(self):
        if self.solved_date:
            return (self.solved_date - self.created_date).days
        return None


class ArticleReviewDeviceMention(models.Model):
    DEVICE_TYPE = (
        ("similar", "Similar"),
        ("competitor", "competitor"),
        ("under_evaluation", "Under Evaluation")
    )

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    article_review = models.ForeignKey(ArticleReview, on_delete=models.CASCADE)
    mentions_count = models.IntegerField()
    device_type = models.CharField(choices=DEVICE_TYPE)
