from email.policy import default
from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, Button, Row
from django.db.models import fields
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django import forms
from django.core.files import File
from django.db.models import Q
from backend.logger import logger
import json 

from s3direct.widgets import S3DirectWidget

from client_portal.models import Project
from .models import (
    Article,
    LiteratureReviewSearchProposal,
    ArticleReview,
    AdverseEventReview,
    AdverseEvent,
    AdverseRecall,
    ClinicalLiteratureAppraisal,
    LiteratureSearch,
    NCBIDatabase,
    SearchProtocol,
    Device,
    KeyWord,
    CustomKeyWord,
    ExclusionReason,
    LiteratureReview,
    Client,
    Device,
    Manufacturer,
    #LiteratureReviewIntake,
    AdversDatabaseSummary,
    AdverseRecallReview,
    FinalReportConfig,
    SearchParameter,
    AppraisalExtractionField,
    ArticleTag,
)
from lit_reviews.helpers.search_terms import get_search_protocol_scope_field_label
from client_portal.models import Project
import floppyforms

class S3DirectUploadForm(forms.Form):
    file = forms.URLField(widget=S3DirectWidget(dest='citemied_files'), label=False)

class QuickExcludeForm(forms.Form):
    def __init__(self, *args, **kwargs):

        # print(kwargs)

        reasons_tupe_list = kwargs.pop("reasons_tupe_list")
        article_review_id = kwargs.pop("article_review_id")

        super(QuickExcludeForm, self).__init__(*args, **kwargs)
        self.fields["reason"] = forms.ChoiceField(choices=reasons_tupe_list)
        self.fields["reason"].widget.attrs = {
            "id": "exclude{0}".format(article_review_id),
            "class": "reason-selectbox",
        }


class uploadFullText(forms.Form):
    def __init__(self, *args, **kwargs):
        article_id = kwargs.pop("article_id")
        super(uploadFullText, self).__init__(*args, **kwargs)
        self.fields["file"] = forms.FileField()
        self.fields["file"].widget.attrs = {"id": "article{0}".format(article_id)}


## this is how to pass choice fields.
# tup_list.append( (trade_str, trade_str) )
# return tuple(tup_list)

from django.forms.widgets import TextInput
class KeyWordForm(forms.ModelForm):
    class Meta:
        model = KeyWord
        fields = [
            "population","population_color",
            "intervention","intervention_color",
            "comparison","comparison_color",
            "outcome","outcome_color",
            "exclusion","exclusion_color"
            ]
        widgets = {
            'population_color': TextInput(attrs={'type': 'color','class': 'color-picker-section'}),
            'intervention_color': TextInput(attrs={'type': 'color','class': 'color-picker-section'}),
            'comparison_color': TextInput(attrs={'type': 'color','class': 'color-picker-section'}),
            'outcome_color': TextInput(attrs={'type': 'color','class': 'color-picker-section'}),
            'exclusion_color': TextInput(attrs={'type': 'color','class': 'color-picker-section'}),
        }

class CustomKeyWordForm(forms.ModelForm):
    class Meta:
        model = CustomKeyWord
        fields = [
            "custom_kw","custom_kw",
            "custom_kw_color","custom_kw_color",
            ]
        widgets = {
            'custom_kw': TextInput(attrs={'class': 'custom-keyword'}),
            'custom_kw_color': TextInput(attrs={'type': 'color','class': 'custom-keyword-color-picker'})
        }    


class ArticleReviewForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
            queryset=ArticleTag.objects.all(),
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )

    def __init__(self, *args, **kwargs):
        literature_review_id = kwargs.pop("literature_review_id")
        exclude_reasons = ExclusionReason.objects.filter(literature_review__id=literature_review_id)
        reasons_tupe_list = []
        for ex_reason in exclude_reasons:
            reasons_tupe_list.append((ex_reason.reason,ex_reason.reason))

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        project_tags = ArticleTag.objects.filter(literature_review__id=literature_review_id)
        self.fields['tags'].queryset = project_tags
        self.fields['tags'].initial = self.instance.tags.all()
        if not project_tags.count():
            self.fields['tags'].widget = self.fields['tags'].hidden_widget()

        self.fields["exclusion_reason"] = forms.ChoiceField(choices=reasons_tupe_list)
        self.helper.form_style = "inline"
        self.helper.template = "bootstrap4/table_inline_formset.html"
        self.fields["exclusion_reason"].widget.attrs = {
            "class": "form-control-exclusion-reason",
        }
        self.fields["notes"].label = "Article Notes"
        self.fields["exclusion_reason"].required = False 
        self.helper.layout = Layout(
            InlineField("state", css_class="form-control mr-2"),
        )
        self.helper.add_input(Submit("submit", "Save"))
        self.fields["state"].label = False

    class Meta:
        # print(literature_review_id)

        model = ArticleReview
        fields = [
            "tags",
            "notes",
            "state",
            "exclusion_reason",
        ]
        labels = {
            "exclusion_reason": _("If Excluded, please provide a reason"),
        }  # "sota_state", "sota_exclusion_reason"


    def clean(self):
        super().clean()
        state = self.cleaned_data.get('state')
        if state == ArticleReview.ArticleReviewState.EXCLUDED:
            if not self.cleaned_data.get("exclusion_reason"):
                raise forms.ValidationError({"exclusion_reason": ["If you are excluding this article please provide a reason why."]})
        else: 
            self.cleaned_data["exclusion_reason"] = None
        return self.cleaned_data

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Add Tags
        for tag in self.cleaned_data["tags"]:
            self.instance.tags.add(tag)

        # Remove Tags 
        for tag in self.instance.tags.all():
            if tag not in self.cleaned_data["tags"]:
                self.instance.tags.remove(tag)

        return self.instance

class AdverseEventReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_style = "inline"
        self.helper.template = "bootstrap4/table_inline_formset.html"
        self.helper.layout = Layout(
            InlineField("exclusion_reason", css_class="form-control ml-2 col-5"),
            InlineField("state", css_class="form-control mr-2"),
        )
        self.helper.add_input(Submit("submit", "Save"))
        self.fields["state"].label = False

    class Meta:
        model = AdverseEventReview
        fields = [
            "state",
        ]
        # labels = {
        #     'exclusion_reason': _('If Excluded, please provide a reason'),
        # }

    def clean(self):
        super().clean()
        # TODO handle no exclusion reason
        # if any(self.errors):
        #     return
        # if self.cleaned_data["state"] == ArticleReview.ArticleReviewState.EXCLUDED and not self.cleaned_data["exclusion_reason"]:
        #     raise forms.ValidationError("If you are excluding this article please provide a reason why.")
        # return self.cleaned_data


class ClinicalLiteratureAppraisalHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_style = "inline"
        self.template = "bootstrap4/table_inline_formset.html"
        self.form_method = "post"
        self.layout = Layout(
            InlineField("appropriate_device"),
            InlineField("appropriate_application"),
            InlineField("appropriate_patient_group"),
            InlineField("acceptable_collation_choices"),
            InlineField("data_contribution"),
            InlineField("outcome_measures"),
            InlineField("appropriate_followup"),
            InlineField("statistical_significance"),
            InlineField("clinical_significance"),
            InlineField("included"),
            # InlineField("sota_inclusion"),
            InlineField("sota_exclusion_reason"),
            InlineField("justification"),
        )
        self.add_input(Submit("submit", "Save"))


class ClinicalLiteratureAppraisalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ClinicalLiteratureAppraisalForm, self).__init__(*args, **kwargs)
        self.fields["included"].widget.attrs["class"] = "included"
        self.fields["is_sota_article"].label = "Is this article a SoTA Article?"
        self.fields["is_sota_article"].widget.attrs["class"] = "is_sota_article"
        self.fields["justification"].widget.attrs["class"] = "justification"

    class Meta:
        model = ClinicalLiteratureAppraisal
        fields = [
            "included",
            "justification",
            "is_sota_article",
        ]

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_style = "inline"
        helper.form_method = "post"
        helper.layout = Layout(
            InlineField("included"),
            InlineField("justification"),
            InlineField("is_sota_article"),
        )
        helper.add_input(Submit("submit", "Save"))
        return helper

class DateInput(forms.DateInput):
    input_type = 'date'


class LitReviewSearchProtocolForm(forms.ModelForm):
    class Meta:
        model = SearchProtocol
        fields = [
            "device_description",
            "intended_use",
            "indication_of_use",
            "lit_start_date_of_search",
            "ae_start_date_of_search",
            "ae_date_of_search",
            "lit_date_of_search",
            "max_imported_search_results",
            "comparator_devices",
            "sota_product_name",
            "sota_description",
            "safety_claims",
            "performance_claims",
            "other_info",
            "scope",
            "preparer",
            "lit_searches_databases_to_search",
            "ae_databases_to_search",
            "vigilance_inclusion_manufacturers",
            "vigilance_inclusion_keywords",
        ]
        widgets = {
            'ae_date_of_search': DateInput(),
            'lit_date_of_search': DateInput(),
            'lit_start_date_of_search': DateInput(),
            'ae_start_date_of_search': DateInput(),
            'scope':forms.Textarea,
             
        }

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.form_tag = False
        # helper.add_input(Submit("submit", "Save"))
        return helper

    def __init__(self, *args, **kwargs):
        super(LitReviewSearchProtocolForm, self).__init__(*args, **kwargs)
        not_isrecall = Q( Q(is_recall=None) | Q(is_recall=False) )
        not_isae = Q( Q(is_ae=None) | Q(is_ae=False) )
        not_recall_and_not_ae = Q( not_isrecall & not_isae)
        isrecall_or_isae = Q( Q(is_ae=True) | Q(is_recall=True) )
        self.fields['lit_searches_databases_to_search'].queryset = NCBIDatabase.objects.filter(not_recall_and_not_ae, is_archived=False)
        self.fields['ae_databases_to_search'].queryset = NCBIDatabase.objects.filter(isrecall_or_isae, is_archived=False)
        self.fields["lit_start_date_of_search"].label = "Literature Search Start Date"
        self.fields["lit_searches_databases_to_search"].label = "Clinical Literature Databases to Search"
        self.fields["ae_start_date_of_search"].label = "Adverse Event Search Start Date"
        self.fields["ae_date_of_search"].label = "Adverse Event Search End Date"
        self.fields["lit_date_of_search"].label = "Literature Search End Date"
        self.fields["comparator_devices"].label = "Comparator devices ( Note: Please write each comparator device separated by a comma! )"
        self.fields["scope"].label = "Scope section of protocol input (note: Please complete the following paragraph by filling in the text box below)"

class PMCFSearchProtocolForm(forms.ModelForm):
    class Meta:
        model = SearchProtocol
        fields = [
            "device_description",
            "intended_use",
            "indication_of_use",
            "vigilance_inclusion_manufacturers",
            "vigilance_inclusion_keywords",
            "ae_date_of_search",
            "lit_date_of_search",
            "lit_start_date_of_search",
            "ae_start_date_of_search",
            "max_imported_search_results",
            "max_articles_reviewed",
            "comparator_devices",
            "sota_product_name",
            "sota_description",
            "safety_claims",
            "performance_claims",
            "other_info",
            "scope",
            "preparer",
            "lit_searches_databases_to_search",
            "ae_databases_to_search",
        ]
        widgets = {
            'ae_date_of_search': DateInput(),
            'lit_date_of_search': DateInput(),
        }

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("device_description"),
            Field("intended_use"),
            Field("indication_of_use"),
            Field("vigilance_inclusion_manufacturers"),
            Field("vigilance_inclusion_keywords"),
            Field("ae_start_date_of_search"),
            Field("lit_start_date_of_search"),
            Field("ae_date_of_search"),
            Field("lit_date_of_search"),
            Field("max_imported_search_results"),
            Field("max_articles_reviewed"),
            Field("comparator_devices"),
            Field("sota_product_name"),
            Field("sota_description"),
            Field("safety_claims"),
            Field("performance_claims"),
            Field("other_info"),
            Field("scope"),
            Field("preparer"),
            Field("lit_searches_databases_to_search"),
            Field("ae_databases_to_search"),
        )
        helper.form_tag = False
        # helper.add_input(Submit("submit", "Save"))
        return helper

    def __init__(self, *args, **kwargs):
        super(PMCFSearchProtocolForm, self).__init__(*args, **kwargs)
        not_isrecall = Q( Q(is_recall=None) | Q(is_recall=False) )
        not_isae = Q( Q(is_ae=None) | Q(is_ae=False) )
        not_recall_and_not_ae = Q( not_isrecall & not_isae)
        isrecall_or_isae = Q( Q(is_ae=True) | Q(is_recall=True) )
        self.fields['lit_searches_databases_to_search'].queryset = NCBIDatabase.objects.filter(not_recall_and_not_ae, is_archived=False)
        self.fields['ae_databases_to_search'].queryset = NCBIDatabase.objects.filter(isrecall_or_isae, is_archived=False)
        self.fields["lit_date_of_search"].label = "Lit End Date of search"
        self.fields["comparator_devices"].label = "Comparator devices ( Note: Please write each comparator device separated by a comma! )"
        self.fields["scope"].label = "Scope section of protocol input (note: Please complete the following paragraph by filling in the text box below)"
        

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["name", "classification", "markets"]

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("name"),
            Field("classification"),
            Field("manufacturer", css_class="manufacturer-input"),
            Field("markets"),
        )
        helper.add_input(Submit("submit", "Save"))
        self.fields['name'].widget.attrs.update({'placeholder': 'Enter Device Name'})
        self.fields['classification'].widget.attrs.update({'placeholder': 'Enter Device classification'})
        self.fields['markets'].widget.attrs.update({'placeholder': 'Enter Device markets'})

        return helper


class CreateLiteratureReviewForm(forms.ModelForm):
    project_type_choices = (
        ("lit_review", "Lit. Review"),
        ("CER", "CER"),
        ("PMCF", "PMCF"),
        ("Vigilance", "Vigilance"),
    )
    project_type = forms.ChoiceField(choices=project_type_choices, required=True)

    def __init__(self, *args, **kwargs):
        super(CreateLiteratureReviewForm, self).__init__(*args, **kwargs)
        self.fields[
            "authorized_users"
        ].help_text = (
            "Hold down “Control”, or “Command” on a Mac, to select more than one."
        )

    def save(self, *args, **kwargs):
        project_type = self.cleaned_data.pop("project_type")
        lit_review = super(CreateLiteratureReviewForm, self).save(*args, **kwargs)
        Project.objects.create(
            client=lit_review.client,
            type=project_type,
            lit_review=lit_review,
        )

        return lit_review

    class Meta:
        model = LiteratureReview
        fields = (
            "client",
            "device",
            #"intake",
            "authorized_users",
            "project_type",
        )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("client", css_class="client-input"),
            Field("device", css_class="device-input"),
           # Field("intake", css_class="intake-input"),
            Field("authorized_users"),
            Field("project_type"),
        )
        helper.add_input(Submit("submit", "Save"))
        return helper


class CreateClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            "name",
            "short_name",
            "long_name",
            "full_address_string",
            "logo",
        )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("name"),
            Field("short_name"),
            Field("long_name"),
            Field("full_address_string"),
            Field("logo"),
        )
        self.fields['name'] = forms.CharField()
        self.fields['short_name'] = forms.CharField()
        self.fields['long_name'] = forms.CharField()
        self.fields['full_address_string'] = forms.CharField()

        self.fields['name'].widget.attrs.update({'placeholder': 'Enter Client Name'})
        self.fields['short_name'].widget.attrs.update({'placeholder': 'Enter Short Name'})
        self.fields['long_name'].widget.attrs.update({'placeholder': 'Enter Long Name'})
        self.fields['full_address_string'].widget.attrs.update({'placeholder': 'Enter Full Address'})

       
        helper.add_input(Submit("submit", "Save"))
        return helper



class CreateDeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = (
            "name",
            "manufacturer",
            "classification",
            "markets",
        )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("name"),
            Field("manufacturer", css_class="manufacturer-input"),
            Field("classification"),
            Field("markets"),
        )
        helper.add_input(Submit("submit", "Save"))
        return helper


class CreateManufacturerForm(forms.ModelForm):
    class Meta:
        model = Manufacturer
        fields = ("name",)

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("name"),
        )
        helper.add_input(Submit("submit", "Save"))
        return helper


# class CreateLiteratureReviewIntakeForm(forms.ModelForm):
#     class Meta:
#         model = LiteratureReviewIntake
#         fields = ("client", "device", "markets")

#     @property
#     def helper(self):
#         helper = FormHelper()
#         helper.form_method = "post"
#         helper.layout = Layout(
#             Field("client", css_class="client-input"),
#             Field("device", css_class="device-input"),
#             Field("markets"),
#         )
#         helper.add_input(Submit("submit", "Save"))
#         return helper


class ExclusionReasonForm(forms.ModelForm):
    class Meta:
        model = ExclusionReason
        fields = ("reason",)

class AdversDatabaseSummaryForm(forms.ModelForm):
    class Meta:
        model = AdversDatabaseSummary
        fields = ("database", "summary")
        widgets = {
            'summary': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
            "database": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.fields['summary'].label = "Adverse Database Summary"

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_tag = False
        return helper

CHOICES = (
    ("AE", "Adverse Event"),
    ("RE", "Recall")
)

SERVERITY_CHOICES = (
    ("Death", "Death"),
    ("Injury", "Injury"),
    ("Malfunction", "Malfunction"),
    ("Other", "Other"),
    ("NA", "NA"),
    ("Mild", "Mild"),
    ("Medium", "Medium"),
    ("Severe", "Severe"),
)

def get_choices_for_search(db_name, lit_id):
    lit_searches = LiteratureSearch.objects.filter(db__name=db_name,  literature_review_id=lit_id)
    choices = []
    for search in lit_searches:
        choices.append(
            (search.id, f"{search.term} - {search.db}")
        )

    return choices

class AdverseEventorRecallForm(forms.Form):

    type = forms.CharField(required=False)
    severity = forms.ChoiceField(required=False, choices=SERVERITY_CHOICES)
    link = forms.CharField(required=False)
    pdf = forms.FileField(required=False)
    ae_or_recall = forms.ChoiceField(choices=CHOICES)
    lit_id = forms.CharField(widget=forms.TextInput(attrs={'type':'hidden'}))
    db_name = forms.CharField(widget=forms.TextInput(attrs={'type':'hidden'}))
    event_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control', 
                'placeholder': 'Select a date',
                'type': 'date'
            }
        )
    )

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        db_name = kwargs.get("initial").get("db_name")
        lit_id = kwargs.get("initial").get("lit_id")
        self.fields['search'] = forms.ChoiceField(choices=get_choices_for_search(db_name, lit_id))
        self.fields['ae_or_recall'].label = "Adverse Event or Recall"
        self.helper = FormHelper()
        self.helper.form_tag = False

    def save(self):
        ae_or_recall = self.cleaned_data.get("ae_or_recall")
        type = self.cleaned_data.get("type")
        severity = self.cleaned_data.get("severity")
        link = self.cleaned_data.get("link")
        pdf = self.cleaned_data.get("pdf")
        search_id = self.cleaned_data.get("search")
        event_date = self.cleaned_data.get("event_date")
        db_name = self.cleaned_data.get("db_name")
        search = LiteratureSearch.objects.get(id=search_id)
        db = NCBIDatabase.objects.get(name=db_name)

        if ae_or_recall == "AE":
            instance = AdverseEvent.objects.create(
                manual_type=type,
                manual_severity=severity,
                manual_link=link,
                db=db,
                event_date=event_date,
            )

            search.ae_events.add(instance)

            AdverseEventReview.objects.create(ae=instance, search=search, state="IN")

        else:
            instance = AdverseRecall.objects.create(
                manual_type=type,
                manual_severity=severity,
                manual_link=link,
                db=db,
                event_date=event_date,
            )
            AdverseRecallReview.objects.create(ae=instance, search=search, state="IN")

            search.ae_recalls.add(instance)

        if pdf:
            TMP_ROOT = settings.TMP_ROOT
            FILE_PATH = TMP_ROOT +  "/search" + str(pdf)
            with open(FILE_PATH, "wb") as f:
                for chunk in pdf.chunks():
                    f.write(chunk)

            f = open(FILE_PATH, "rb")

            instance.manual_pdf = File(f)
            instance.save()


        return instance 

class AdverseEventForm(forms.ModelForm):
    event_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control', 
                'placeholder': 'Select a date',
                'type': 'date'
            }
        )
    )
    manual_severity = forms.ChoiceField(required=False, choices=SERVERITY_CHOICES)

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["manual_type"].label = "Type"
        self.fields["manual_severity"].label = "Severity"
        self.fields["manual_link"].label = "Link"
        self.fields["manual_pdf"].label = "PDF"
        
    class Meta:
        model = AdverseEvent
        fields = [ 
            "manual_type",
            "manual_severity",
            "manual_link",
            "manual_pdf",
            "event_date",
        ]

class AdverseRecallForm(forms.ModelForm):
    event_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(
            format=('%Y-%m-%d'),
            attrs={'class': 'form-control', 
                'placeholder': 'Select a date',
                'type': 'date'
            }
        )
    )
    manual_severity = forms.ChoiceField(required=False, choices=SERVERITY_CHOICES)

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["manual_type"].label = "Type"
        self.fields["manual_severity"].label = "Severity"
        self.fields["manual_link"].label = "Link"
        self.fields["manual_pdf"].label = "PDF"

    class Meta:
        model = AdverseRecall
        fields = [
            "manual_type",
            "manual_severity",
            "manual_link",
            "manual_pdf",
            "event_date",
        ]

class ManualAdverseEventReview(forms.ModelForm):

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = AdverseEventReview
        fields = ("search",)


class ManualAdverseRecallReview(forms.ModelForm):

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = AdverseRecallReview
        fields = ("search",)

class FinalReportConfigForm(forms.ModelForm):
    class Meta:
        model = FinalReportConfig
        fields = [
            "literature_review",
            "sota_suitability", 
            "appropriate_device",
            "appropriate_application",
            "appropriate_patient_group",
            "acceptable_collation_choices",
            "data_contribution",
            "grade",
            "design_yn", 
            "outcomes_yn", 
            "followup_yn",  
            "stats_yn", 
            "study_size_yn", 
            "clin_sig_yn", 
            "clear_conc_yn", 
            "safety", 
            "performance", 
            "adverse_events", 
            "sota", 
            "guidance", 
            "other", 
            "study_design", 
            "total_sample_size", 
            "objective", 
            "treatment_modality", 
            "study_conclusions", 
            "outcome_measures", 
            "appropriate_followup", 
            "statistical_significance", 
            "clinical_significance", 
            "justification", 
        ]
        widgets = {
            "literature_review": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = (
            "title",
            "abstract",
            "citation",
            "pubmed_uid",
            "pmc_uid",
            "doi",
            "full_text",
        )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("title"),
            Field("abstract"),
            Field("citation"),
            Field("pubmed_uid"),
            Field("pmc_uid"),
            Field("doi"),
            Field("full_text")   
        )
        helper.add_input(Submit("submit", "Save"))
        return helper


class ConfigForm(forms.Form):
    def get_field_choices(self, param):
        param_options = param.options.split(",")
        return [(c, c) for c in param_options]

    def build_field_type(self, param):
        if param.type == "DP":
            choices = self.get_field_choices(param)
            value = param.value
            return forms.ChoiceField(choices=choices, widget=forms.Select(), initial=value, required=False)

        if param.type == "CK":
            choices = self.get_field_choices(param)
            value = param.value
            value_list = param.value.split(",") if value else None
            return forms.MultipleChoiceField(choices=choices, widget=forms.CheckboxSelectMultiple(), initial=value_list, required=False)

        if param.type == "TX":
            value = param.value
            return forms.CharField(initial=value, required=False)

        if param.type == "DT":
            value = param.value
            return forms.DateField(widget=forms.DateInput(
                                format=('%Y-%m-%d'),
                                attrs={'class': 'form-control', 
                                    'placeholder': 'Select a date',
                                    'type': 'date'
                                },
                            ), initial=value, required=False)

    def __init__(self, *args, **kwargs): 
        parameter = kwargs.pop("parameter")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        
        self.fields["param_id"] = forms.IntegerField(widget=forms.HiddenInput(), initial=parameter.id)
        self.fields[parameter.name] = self.build_field_type(parameter)

    def save(self):
        param_id = self.data.get(str(self.prefix)+"-param_id")
        parameter = SearchParameter.objects.get(id=param_id)
        if parameter.type == "CK":  
            value_list = self.data.getlist(str(self.prefix)+"-"+parameter.name)
            value = ",".join(value_list)
        else:
            value = self.data.get(str(self.prefix)+"-"+parameter.name)
        logger.debug("value : "+str(value))
        parameter.value = value
        parameter.save()


class ExtractionFieldForm(forms.Form):
    
    def get_field_choices(self, field):
        field_options = json.loads(field.extraction_field.drop_down_values)
        field_options = [(c, c) for c in field_options]
        return [("", "---------"), *field_options]

    def build_field_type(self, field):
        if field.extraction_field.type == "DROP_DOWN":
            choices = self.get_field_choices(field)
            value = field.value
            if field.extraction_field.name == "sota_suitability" and value:
                value = value.replace(":", "")
            return forms.ChoiceField(choices=choices, widget=forms.Select(), initial=value, required=False)

        if field.extraction_field.type == "TEXT":
            value = field.value
            return forms.CharField(initial=value, required=False)
        
        if field.extraction_field.type == "LONG_TEXT":
            value = field.value
            return forms.CharField(initial=value, required=False, widget=forms.Textarea(attrs={"rows":"9"}))


    def __init__(self, *args, **kwargs): 
        field_obj = kwargs.pop("field_obj")
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.form_show_labels = False
        
        self.fields["obj_id"] = forms.IntegerField(widget=forms.HiddenInput(), initial=field_obj.id)
        self.fields["field_section"] = forms.CharField(widget=forms.HiddenInput(), initial=field_obj.extraction_field.field_section)
        self.fields["extraction_field_number"] = forms.IntegerField(widget=forms.HiddenInput(), initial=field_obj.extraction_field_number)
        
        self.fields[field_obj.extraction_field.name] = self.build_field_type(field_obj)
        if field_obj.extraction_field.description:
            self.fields[field_obj.extraction_field.name].label =  field_obj.extraction_field.description
        elif field_obj.extraction_field_number > 1:
            self.fields[field_obj.extraction_field.name].label = field_obj.extraction_field.name.replace("_", " ").capitalize() + " Sub #" + str(field_obj.extraction_field_number)

    def save(self):
        obj_id = self.data.get(str(self.prefix)+"-obj_id")
        field_obj = AppraisalExtractionField.objects.get(id=obj_id)
        value = self.data.get(str(self.prefix)+"-"+field_obj.extraction_field.name)
        logger.debug("value : "+str(value))
        field_obj.value = value
        field_obj.save()


class UpdateClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            "name",
            "short_name",
            "long_name",
            "full_address_string",
            "logo",
        )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_method = "post"
        helper.layout = Layout(
            Field("name"),
            Field("short_name"),
            Field("long_name"),
            Field("full_address_string"),
            Field("logo"),
        )
        return helper


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project 
        fields = [
            "project_name",
            "type",
            "max_terms",
            "max_hits",
            "max_results",
        ]

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.fields["max_terms"].label = False
        self.fields["max_terms"].widget.attrs = {"class": "numberinput form-control"}
        self.fields["max_hits"].label = False
        self.fields["max_hits"].widget.attrs = {"class": "numberinput form-control"}
        self.fields["max_results"].label = False
        self.fields["max_results"].widget.attrs = {"class": "numberinput form-control"}


class ProjectPublicForm(forms.ModelForm):
    """
    Public project don't need max_terms, max_hits, max_results
    """
    class Meta:
        model = Project 
        fields = [
            "project_name",
            "type",
        ]
