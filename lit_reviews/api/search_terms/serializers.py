from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from lit_reviews.api.search_protocol.serializers import SearchConfigurationSerializer
import datetime

from backend.logger import logger
from lit_reviews.models import (
    LiteratureReview,
    LiteratureSearch,
    LiteratureReviewSearchProposal,
    LiteratureReviewSearchProposalReport,
    NCBIDatabase,
    SearchTermsPropsSummaryReport,
    SearchTermValidator,
    SearchProtocol,
    SearchTermsPropsSummaryReport,
    ArticlePreview,
    ArticleReview,
    SearchTermPreview,
    SearchConfiguration
)
# from lit_reviews.tasks import (
#     update_search_term,
# )

class NCBIDatabaseSerializer(ModelSerializer):
    search_configuration = SerializerMethodField()

    class Meta:
        model = NCBIDatabase
        fields = '__all__'

    def get_search_configuration(self,obj): 
        literature_review = self.context.get('literature_review')        
        results = SearchConfiguration.objects.filter(database=obj.name,literature_review=literature_review)
        return SearchConfigurationSerializer(results, many=True).data

class LiteratureReviewSearchProposalReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = LiteratureReviewSearchProposalReport 
        fields = "__all__"

        
class LiteratureReviewSearchProposalSerializer(serializers.ModelSerializer):
    db = serializers.CharField(source="db.displayed_name")
    db_entrez_enum = serializers.CharField(source="db.entrez_enum")
    db_is_ae = serializers.CharField(source="db.is_ae")
    db_is_recall = serializers.CharField(source="db.is_recall")

    class Meta:
        model = LiteratureReviewSearchProposal
        fields = "__all__"

class SearchTermsPropsSummaryReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = SearchTermsPropsSummaryReport
        fields = "__all__"

class SearchTermValidatorSerializer(serializers.ModelSerializer):

    class Meta:
        model = SearchTermValidator
        fields = "__all__"

class SearchProtocolSerializer(serializers.ModelSerializer):
    lit_start_date_of_search = serializers.SerializerMethodField()
    ae_start_date_of_search = serializers.SerializerMethodField()

    class Meta:
        model = SearchProtocol
        fields = "__all__"

    def get_lit_start_date_of_search(self, obj):
        if obj.lit_start_date_of_search:
            return obj.lit_start_date_of_search
        elif obj.lit_date_of_search:
            years_back = obj.years_back
            days_back = 360*years_back
            start_date = obj.lit_date_of_search - datetime.timedelta(days=days_back)
            obj.lit_start_date_of_search = start_date
            obj.save()
            return start_date
        else:
            return ""
    
    def get_ae_start_date_of_search(self, obj):
        if obj.ae_start_date_of_search:
            return obj.ae_start_date_of_search
        elif obj.ae_date_of_search:
            years_back = obj.ae_years_back
            days_back = 360*years_back
            start_date = obj.ae_date_of_search - datetime.timedelta(days=days_back)
            obj.ae_start_date_of_search = start_date
            obj.save()
            return start_date
        else:
            return ""

class CreateNewSearchTermSerializer(serializers.Serializer):
    term = serializers.CharField()
    is_sota_term = serializers.BooleanField()
    entrez_enums = serializers.ListField()
    clinical_trials_search_field = serializers.CharField(required=False)
    maude_search_field = serializers.CharField(required=False)
    term_type = serializers.CharField(required=False)

    def validate(self, data):
        term = data.get("term")
        lit_review_id = self.context.get("lit_review_id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        # there shouldn't be an existing search with the same term!
        if LiteratureSearch.objects.filter(term=term, literature_review = lit_review).exists():
            raise serializers.ValidationError(f"There is already a Search with the exact same term you are trying to add '{term}' please update the existing one instead.")
        return data

    def create(self, validated_data):
        from lit_reviews.helpers.search_terms import update_search_terms

        user_id = self.context.get("user_id")
        lit_review_id = self.context.get("lit_review_id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)
        db = NCBIDatabase.objects.get(entrez_enum=validated_data.get("entrez_enums")[0])
        clinical_trials_search_field = validated_data.pop("clinical_trials_search_field", None)
        maude_search_field = validated_data.pop("maude_search_field")
        
        new_prop = LiteratureReviewSearchProposal.objects.create(
            literature_review = lit_review,
            term = validated_data.get("term"),
            db = db,
            result_count = -1,
        )
        new_search = LiteratureSearch.objects.create(
            literature_review = lit_review,
            db = db,
            result_count = -1,
            term = validated_data.get("term"),
            search_label = validated_data.get("term_type"),
        )
        new_prop.literature_search = new_search
        new_prop.save()
        
        # udpating search field
        if clinical_trials_search_field and new_search.db.entrez_enum == "ct_gov":
            new_search.advanced_options = {"search_field" : clinical_trials_search_field}
            new_search.save()
        elif maude_search_field and new_search.db.entrez_enum == "maude":
            new_search.advanced_options = {"search_field" : maude_search_field} 
            new_search.save()

        update_search_terms(new_prop.id, lit_review_id, **validated_data, user_id=user_id)
        return validated_data.get("term")

class UpdateSearchTermSerializer(serializers.Serializer):
    update_type = serializers.CharField(required=False)
    prop_id = serializers.IntegerField()
    lit_review_id = serializers.IntegerField()
    term = serializers.CharField()
    is_sota_term = serializers.BooleanField()
    entrez_enums = serializers.ListField()
    clinical_trials_search_field = serializers.CharField(required=False)
    maude_search_field = serializers.CharField(required=False)
    term_type = serializers.CharField(required=False)

    def validate_entrez_enums(self, value):
        """
        Check if the list field is empty.
        """
        if not len(value):
            raise serializers.ValidationError("please provide at least one database to update your term")
        return value

    def create(self, validated_data):
        from lit_reviews.helpers.search_terms import update_search_terms

        user_id = self.context.get("user_id")
        if validated_data.get("update_type"):
            validated_data.pop("update_type")
        
        clinical_trials_search_field = validated_data.pop("clinical_trials_search_field", None)
        maude_search_field = validated_data.pop("maude_search_field", None)
        term_type = validated_data.pop("term_type")
        # update_search_term.delay(**validated_data, user_id=user_id)
        update_search_terms(
            **validated_data, 
            user_id=user_id, 
            clinical_trials_search_field=clinical_trials_search_field, 
            maude_search_field=maude_search_field,
            term_type=term_type
        )
        return validated_data.get("term")
    
class SplitTermSerializer(serializers.Serializer):
    update_type = serializers.CharField(required=False)
    prop_ids = serializers.ListField()
    term = serializers.CharField()
    is_sota_term = serializers.BooleanField()
    clinical_trials_search_field = serializers.CharField(required=False)
    maude_search_field = serializers.CharField(required=False)

    def validate_prop_ids(self, value):
        """
        Check if the list field is empty.
        """
        if not len(value):
            raise serializers.ValidationError("please provide at least one database to update your term")
        return value

    def create(self, validated_data):
        from lit_reviews.helpers.search_terms import update_search_proposal
        from lit_reviews.tasks import fetch_preview_and_expected_results
        
        validated_data.pop("update_type")
        prop_ids = validated_data.pop("prop_ids")
        term = validated_data.get("term")
        lit_review = self.context.get("lit_review")
        user_id = self.context.get("user_id")

        report = LiteratureReviewSearchProposalReport.objects.filter(term=term, literature_review=lit_review).order_by("id").first()
        if not report:
            report = LiteratureReviewSearchProposalReport.objects.create(term=term, literature_review=lit_review)
        props = LiteratureReviewSearchProposal.objects.filter(
            id__in=prop_ids, 
            literature_review=lit_review
        )
        
        for prop in props:
            update_search_proposal(
                report,
                prop,
                **validated_data,
            )

        report.status = "FETCHING_PREVIEW"
        report.save()
        fetch_preview_and_expected_results.delay(term, lit_review.id, user_id=user_id)
        return validated_data.get("term")
    
class ResultSummarySerializer(serializers.ModelSerializer):

    class Meta:
        model = SearchTermsPropsSummaryReport
        fields = "__all__"

class ArticlePreviewSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ArticlePreview
        fields = "__all__"

class SearchTermPreviewSerializer(serializers.ModelSerializer):
    # preview_articles = ArticlePreviewSerializer(many=True)

    class Meta:
        model = SearchTermPreview
        fields = "__all__"

class SearchTermSerializer(serializers.Serializer):
    report = LiteratureReviewSearchProposalReportSerializer()
    expected_result_count = serializers.IntegerField()
    proposal = LiteratureReviewSearchProposalSerializer()
    is_search_file = serializers.BooleanField()
    preview = SearchTermPreviewSerializer()
    count = serializers.CharField()
    scraper_error = serializers.CharField()
    search_field = serializers.CharField()
    term_type = serializers.CharField()