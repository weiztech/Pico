# serializers.py
import datetime, pytz
from django.core.files import File
import pandas as pd 
from backend.logger import logger
from rest_framework import serializers 
from lit_reviews.models import (
    LiteratureSearch,
    NCBIDatabase,   
    Article,
    ArticleReview,
    ClinicalLiteratureAppraisal,
    AppraisalExtractionField
)
from lit_reviews.database_imports.utils import parse_one_off_ris
from lit_reviews.tasks import retain_articles_async, generate_highlighted_pdf_async
from lit_reviews.helpers.generic import create_tmp_file
from lit_reviews.helpers.search_terms import get_search_date_ranges
from lit_reviews.helpers.aws_s3 import get_preview_url_from_instance
from lit_reviews.api.articles.serializers import ArticleTagSerializer
from lit_reviews.helpers.ai import appraisal_ai_extraction_generation

class NCBIDatabaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = NCBIDatabase
        fields = "__all__"


class LiteratureSearchSerializer(serializers.ModelSerializer):
    not_run_or_excluded = serializers.BooleanField()
    is_ae_not_maude = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    none_excluded = serializers.BooleanField()
    limit_excluded = serializers.BooleanField()
    db = NCBIDatabaseSerializer()
    db_name = serializers.CharField(source="db.name")
    term_duplicates = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    maude_search_field = serializers.SerializerMethodField()

    def get_term_duplicates(self, obj):
        return len(
                ArticleReview.objects.filter(
                    search__id=obj.id, state="D"
                )
            )

    def get_start_date(self, obj):
        start_date, end_date = get_search_date_ranges(obj)
        if start_date:
            return start_date.strftime("%d-%m-%Y")
    
    def get_end_date(self, obj):
        start_date, end_date = get_search_date_ranges(obj)
        if end_date:
            return end_date.strftime("%d-%m-%Y")
    
    def get_maude_search_field(self, obj):
        return obj.advanced_options and obj.advanced_options.get("search_field", None)
    
    class Meta:
        model = LiteratureSearch
        fields = "__all__"


class UploadOwnCitationsSerializer(serializers.Serializer):
    database = serializers.CharField()
    file = serializers.FileField()
    external_db_name = serializers.CharField(required=False)
    external_db_url = serializers.CharField(required=False)

    def create(self, validated_data):
        db_name = validated_data.get("database")
        external_db_name = validated_data.get("external_db_name")
        external_db_url = validated_data.get("external_db_url")
        file = validated_data.get("file")

        if db_name == "external":
            db = NCBIDatabase.objects.filter(name=external_db_name, is_external=True).first()
            if not db:
                db = NCBIDatabase.objects.create(
                    name=external_db_name,
                    displayed_name=external_db_name,
                    is_archived=True,
                    is_external=True,
                    url=external_db_url,
                )
                
        else:
            db = NCBIDatabase.objects.get(name=db_name)        
        
        literature_review = self.context.get("literature_review", None)
        tmp_file = create_tmp_file(file.name, file.read())
        search = LiteratureSearch.objects.get_or_create(
            literature_review = literature_review,
            term = "One-Off Manufacturer Search",
            db=db,
        )[0]
        search.import_status = "RUNNING"
        search.error_msg = None
        search.script_time = datetime.datetime.now(pytz.utc)
        search.save()
        results = parse_one_off_ris(tmp_file, literature_review.id, search.id, True)  

        if results["status"] == "COMPLETE": 
            results["search"] = search.id   
            retain_articles_async.delay(search.id)    
            return results
        
        else:
            count = results["count"]
            raise serializers.ValidationError(f"The file you've uploaded countains {count} results which exceeds the max you have set under the Search Protocol View")


class ArticleSerializer(serializers.ModelSerializer):
    keywords = serializers.SerializerMethodField()

    def get_keywords(self, obj):
        if obj.keywords:
            return obj.keywords.split(",")
        return None

    class Meta:
        model = Article
        fields = "__all__"

class ArticleReviewSerializer(serializers.ModelSerializer):
    article = ArticleSerializer()
    search = LiteratureSearchSerializer()
    tags = ArticleTagSerializer(many=True)
    full_text_pdf = serializers.SerializerMethodField()

    class Meta:
        model = ArticleReview
        fields = "__all__"

    def get_full_text_pdf(self, obj):
        if obj.article.full_text and obj.article.full_text.url:
            return get_preview_url_from_instance(obj.article.full_text)
        return None


class AppraisalExtractionFieldSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='extraction_field.name', read_only=True)
    description = serializers.CharField(source='extraction_field.description', read_only=True)
    field_type = serializers.CharField(source='extraction_field.type', read_only=True)
    field_section = serializers.CharField(source='extraction_field.field_section', read_only=True)
    ai_prompte = serializers.CharField(source='extraction_field.ai_prompte', allow_null=True , read_only=True)
    drop_down_values = serializers.CharField(source='extraction_field.drop_down_values', allow_null=True , read_only=True)
    
    class Meta:
        model = AppraisalExtractionField
        fields = [
            'id',
            'value',
            'extraction_field_number',
            'name',
            'description',
            'field_type',
            'field_section',
            'ai_prompte',
            'drop_down_values',
            'ai_value',
            'ai_simplified_value',
            'ai_value_status',
        ]
        read_only_fields = [
            'name',
            'description',
            'field_type',
            'field_section',
            'ai_prompte',
            'drop_down_values',
            'ai_value',
            'ai_simplified_value',
        ]


class ClinicalAppraisalListSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="article_review.article.title")
    authors = serializers.SerializerMethodField()
    details_url = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalLiteratureAppraisal
        fields = [
            "id",
            "title",
            "article_review",
            "authors",
            "is_sota_article",
            "app_status",
            "details_url",
        ]

    def get_authors(self, obj):
        if obj.article_review.article.meta_data:
            return obj.article_review.article.meta_data.get("authors")

    def get_details_url(self, obj):
        return obj.get_absolute_url()


class CreateManualAppraisalSerializer(serializers.ModelSerializer):
    database = serializers.PrimaryKeyRelatedField(queryset=NCBIDatabase.objects.all(), write_only=True)

    class Meta:
        model = Article
        fields = [
            "title",
            "abstract",
            "citation",
            "database",
            "pubmed_uid",
            "pmc_uid",
            "full_text",
        ]

    def create(self, validated_data):
        literature_review = self.context.get("literature_review")
        database = validated_data.pop("database")
        article = super().create(validated_data)

        article.literature_review = literature_review
        article.save()

        search_review = LiteratureSearch.objects.get_or_create(
            literature_review = literature_review,
            term = "One-Off Manufacturer Search",
            db=database,
        )[0]
        article_review  = ArticleReview.objects.create(
            article = article,
            search = search_review, 
            state="I"
        )
        article_review.save()
        return article


class ClinicalLiteratureAppraisalSerializer(serializers.ModelSerializer):
    article_review = ArticleReviewSerializer(read_only=True)
    fields = AppraisalExtractionFieldSerializer(many=True, required=False)

    class Meta:
        model = ClinicalLiteratureAppraisal
        fields = '__all__'


    def update(self, instance, validated_data):
        fields_data = self.context['request'].data.get('fields', [])

        # Update extraction fields
        for field_data in fields_data:
            field_id = field_data.get('id')
            value = field_data.get('value')
            extraction_field_number = field_data.get('extraction_field_number', 1)

            if field_id:
                AppraisalExtractionField.objects.filter(
                    id=field_id,
                    clinical_appraisal=instance
                ).update(
                    value=value,
                    extraction_field_number=extraction_field_number
                )

        # Update main appraisal fields
        for attr, value in validated_data.items():
            if attr != 'fields':
                setattr(instance, attr, value)
        instance.save()
        
        return instance

    def validate(self, data):
        # Add any validation rules here
        return data
    

class PDFHighlightingSerializer(serializers.Serializer):
    article_id = serializers.IntegerField()

    def create(self, validated_data):
        article_id = validated_data.get("article_id")
        litreview_id = self.context.get("litreview_id")

        generate_highlighted_pdf_async.delay(litreview_id, article_id)
        return article_id