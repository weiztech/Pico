from django.contrib import admin
from django import forms

from .models import (
    Reviewer,
    Client,
    Manufacturer,
    Device,
    #LiteratureReviewIntake,
    LiteratureReview,
    NCBIDatabase,
    LiteratureSearch,
    Article,
    ArticleReview,
    FullTextRequest,
    ClinicalLiteratureAppraisal,
    NCBIDatabase,
    AdverseEventRegulatoryBody,
    AdverseEventProductCodes,
    AdverseEvent,
    AdverseEventReview,
    #AdverseEventSearch,
    LiteratureReviewSearchProposal,
    SearchProtocol,
    ExclusionReason,
    #AdverseRecallSearch,
    AdverseRecall,
    AdverseRecallReview,
    FinallReportJob,
    AdversDatabaseSummary,
    SearchTermsPropsSummaryReport,
    KeyWord,
    LiteratureReviewSearchProposalReport,
    CustomKeyWord,
    SearchConfiguration,
    SearchParameter,
    ExtractionField,
    AppraisalExtractionField,
    ScraperReport,
    SearchTermValidator,
    ArticleTag,
    Comment,
    DuplicationReport,
    SearchLabelOption,
    DuplicatesGroup,
    LivingReview,
    SupportRequestTicket,
    CustomerSettings
)

class ExtractionFieldAdmin(admin.ModelAdmin):
    model= ExtractionField  
    list_filter = ('is_template',)
    autocomplete_fields = ['literature_review']
    search_fields = ['literature_review']


class ArticleAdmin(admin.ModelAdmin):
    model= Article  
    search_fields = ['citation', 'title'] 

class ArticleReviewAdmin(admin.ModelAdmin):
    model= ArticleReview 
    
class ArticleTagAdmin(admin.ModelAdmin):
    model= ArticleTag 
    autocomplete_fields = ['literature_review']
    list_display = ["id", "name", "description","creator"]

class LiteratureSearchAdmin(admin.ModelAdmin):
    model = LiteratureSearch
    search_fields = ['term']
    autocomplete_fields = ['literature_review','db','ae_events','ae_recalls']
    list_filter = ('import_status',)

    
class LiteratureReviewSearchProposalAdmin(admin.ModelAdmin):
    model = LiteratureReviewSearchProposal
    search_fields = ['term']
    autocomplete_fields = ['literature_review','db','report','literature_search']

class ClientAdmin(admin.ModelAdmin):
    model= Client
    search_fields = ['name']
 
class DeviceAdmin(admin.ModelAdmin):
    model = Device
    search_fields = ['name']
    autocomplete_fields = ['manufacturer']



class LiteratureReviewAdmin(admin.ModelAdmin):
    model = LiteratureReview
    autocomplete_fields = ['client','device',]
    search_fields = ['client__name', 'device__name', 'device__manufacturer__name']
    list_filter = ('is_deleted', 'is_notebook')

    def get_queryset(self, request):
        return LiteratureReview.all_objects.all()
    
class ArticleAdmin(admin.ModelAdmin):
    model = Article
    search_fields = ['title']

class ArticleReviewAdmin(admin.ModelAdmin):
    model = ArticleReview
    autocomplete_fields = ['article','search','potential_duplicate_for']
    search_fields = ['article__title']

class ExclusionReasonAdmin(admin.ModelAdmin):
    model = ExclusionReason
    autocomplete_fields = ['literature_review']

class AdverseEventReviewAdmin(admin.ModelAdmin):
    model = AdverseEventReview
    autocomplete_fields = ['search','ae']

class FullTextRequestAdmin(admin.ModelAdmin):
    model = FullTextRequest
    autocomplete_fields = ['article']

class ClinicalLiteratureAppraisalAdmin(admin.ModelAdmin):
    model = ClinicalLiteratureAppraisal
    autocomplete_fields = ['article_review']
    search_fields = ['article_review__article__title']

class SearchProtocolAdmin(admin.ModelAdmin):
    model = SearchProtocol
    autocomplete_fields = ['literature_review']

class AdverseRecallReviewAdmin(admin.ModelAdmin):
    model = AdverseRecallReview
    autocomplete_fields = ['search']

class FinallReportJobAdmin(admin.ModelAdmin):
    model = FinallReportJob
    #autocomplete_fields = ['literature_review']

class AdversDatabaseSummaryAdmin(admin.ModelAdmin):
    model = AdversDatabaseSummary
    autocomplete_fields = ['literature_review']

class SearchTermsPropsSummaryReportAdmin(admin.ModelAdmin):
    model = SearchTermsPropsSummaryReport
    autocomplete_fields = ['literature_review']

class KeyWordAdmin(admin.ModelAdmin):
    model = KeyWord
    autocomplete_fields = ['literature_review']

class CustomKeyWordAdmin(admin.ModelAdmin):
    model = CustomKeyWord
    autocomplete_fields = ['literature_review']


class NCBIDatabaseAdmin(admin.ModelAdmin):
    model = NCBIDatabase
    search_fields = ['name']

class AdverseEventAdmin(admin.ModelAdmin):
    model = AdverseEvent
    search_fields = ['event_uid']
    autocomplete_fields = ['db']

class AdverseEventRegulatoryBodyAdmin(admin.ModelAdmin):
    model = AdverseEventRegulatoryBody
    search_fields = ['name']

class AdverseEventProductCodesAdmin(admin.ModelAdmin):
    model = AdverseEventProductCodes
    autocomplete_fields = ['source']

class AdverseRecallAdmin(admin.ModelAdmin):
    model = AdverseRecall
    search_fields = ['event_uid']
    autocomplete_fields = ['db']

class ManufacturerAdmin(admin.ModelAdmin):
    model = Manufacturer
    search_fields = ['name']

class ReviewerAdmin(admin.ModelAdmin):
    model = Reviewer
    search_fields = ['first_name']

class LiteratureReviewSearchProposalReportAdmin(admin.ModelAdmin):
    model = LiteratureReviewSearchProposalReport
    search_fields = ['term']
    autocomplete_fields = ['literature_review']

class SearchParameterForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super (SearchParameterForm,self ).__init__(*args,**kwargs) # populates the post
        self.fields['search_config'].queryset = SearchConfiguration.objects.filter(is_template=True)

    class Meta:
        model = SearchParameter
        fields = "__all__"

class SearchConfigurationAdmin(admin.ModelAdmin):
    model = SearchConfiguration
    autocomplete_fields = ['literature_review']
    list_filter = ('is_template',)

class SearchParameterAdmin(admin.ModelAdmin):
    model = SearchParameter
    search_fields = ['name']
    list_filter = ('search_config__is_template',)
    form = SearchParameterForm

class ScraperReportAdmin(admin.ModelAdmin):
    model = ScraperReport
    search_fields = ['search_term']
    autocomplete_fields = ['literature_review', 'search']
    list_filter = ('script_timestamp',)

class AppraisalExtractionFieldAdmin(admin.ModelAdmin):
    model = AppraisalExtractionField
    search_fields = ['clinical_appraisal__article_review__article__title', 'extraction_field__name']
    autocomplete_fields = ['extraction_field', 'clinical_appraisal', 'extraction_field']
    # list_display = ["id", "extraction_field", "clinical_appraisal"]

class CommentAdmin(admin.ModelAdmin):
    model = Comment
    list_display = ["id", "user","article_review", "text","created_at"]

class DuplicationReportAdmin(admin.ModelAdmin):
    model = DuplicationReport
    search_fields = ['literature_review']
    list_filter = ('timestamp',)
    list_display = ["literature_review","status", "timestamp","duplicates_count"]


class SearchLabelOptionAdmin(admin.ModelAdmin):
    list_display = ('label', 'customer_settings')


class DuplicatesGroupAdmin(admin.ModelAdmin):
    model = DuplicatesGroup
    list_display = ["original_article_review"]
    autocomplete_fields = ["original_article_review", "duplicates"]


class LivingReviewAdmin(admin.ModelAdmin):
    model = LivingReview
    autocomplete_fields = ['device','project_protocol',]
    search_fields = ['device', 'project_protocol']

class CustomerSettingsAdmin(admin.ModelAdmin):
    model = CustomerSettings
    autocomplete_fields = ['client']
    search_fields = ['client__name']
    list_display = ['id', 'client', 'full_texts_naming_format', 'automatic_ai_extraction']
    list_filter = ['automatic_ai_extraction', 'full_texts_naming_format']



class SupportRequestTicketAdmin(admin.ModelAdmin):
    model = SupportRequestTicket
    list_display = ["id", "user", "ticket_status", "follow_up_option", "created_date", "solved_date"]
    list_filter = ("ticket_status", "follow_up_option", "created_date", "solved_date")
    search_fields = ["user__username", "user__email", "description"]
    readonly_fields = ("created_date", "updated_date")
    autocomplete_fields = ["user"]
    


# Register your models here.
admin.site.register(ExtractionField, ExtractionFieldAdmin)
admin.site.register(AppraisalExtractionField, AppraisalExtractionFieldAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(ArticleReview, ArticleReviewAdmin)
admin.site.register(LiteratureSearch, LiteratureSearchAdmin)
admin.site.register(LiteratureReviewSearchProposal, LiteratureReviewSearchProposalAdmin)
admin.site.register(LiteratureReview, LiteratureReviewAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(ExclusionReason, ExclusionReasonAdmin)
admin.site.register(AdverseEventReview, AdverseEventReviewAdmin)
admin.site.register(FullTextRequest, FullTextRequestAdmin)
admin.site.register(ClinicalLiteratureAppraisal, ClinicalLiteratureAppraisalAdmin)
admin.site.register(SearchProtocol, SearchProtocolAdmin)
admin.site.register(AdverseRecallReview, AdverseRecallReviewAdmin)
admin.site.register(FinallReportJob, FinallReportJobAdmin)
admin.site.register(AdversDatabaseSummary, AdversDatabaseSummaryAdmin)
admin.site.register(SearchTermsPropsSummaryReport, SearchTermsPropsSummaryReportAdmin)
admin.site.register(KeyWord, KeyWordAdmin)
admin.site.register(CustomKeyWord, CustomKeyWordAdmin)
admin.site.register(NCBIDatabase, NCBIDatabaseAdmin)
admin.site.register(AdverseEvent, AdverseEventAdmin)
admin.site.register(AdverseEventRegulatoryBody, AdverseEventRegulatoryBodyAdmin)
admin.site.register(AdverseEventProductCodes, AdverseEventProductCodesAdmin)
admin.site.register(AdverseRecall, AdverseRecallAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Reviewer, ReviewerAdmin)
admin.site.register(LiteratureReviewSearchProposalReport, LiteratureReviewSearchProposalReportAdmin)
admin.site.register(SearchConfiguration, SearchConfigurationAdmin)
admin.site.register(SearchParameter, SearchParameterAdmin)
admin.site.register(ScraperReport, ScraperReportAdmin)
admin.site.register(SearchTermValidator)
admin.site.register(ArticleTag, ArticleTagAdmin)
admin.site.register(DuplicationReport, DuplicationReportAdmin)
admin.site.register(SearchLabelOption, SearchLabelOptionAdmin)
admin.site.register(DuplicatesGroup, DuplicatesGroupAdmin)
admin.site.register(LivingReview, LivingReviewAdmin)
admin.site.register(SupportRequestTicket, SupportRequestTicketAdmin) 
admin.site.register(CustomerSettings, CustomerSettingsAdmin)
