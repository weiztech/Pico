from django.urls import reverse

from rest_framework import serializers
from lit_reviews.tasks import check_full_article_link_async, appraisal_ai_extraction_generation_async
from lit_reviews.models import (
    ArticleReview, 
    Article, 
    ExclusionReason, 
    NCBIDatabase,
    ArticleTag,
    Comment,
    DuplicatesGroup,
    ClinicalLiteratureAppraisal,
    CustomerSettings,
)
from lit_reviews.helpers.articles import get_customer_settings
from lit_reviews.api.home.serializers import UserSerialzer
from backend.logger import logger

class CreateCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = [
            'article_review',
            'text'
        ]
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerialzer()

    class Meta:
        model = Comment
        fields = ['id', 
                "text",
                "created_at",
                "updated_at",
                "user",
                "article_review"
            ]
   

class ArticleSerializer(serializers.ModelSerializer):
    keywords_list = serializers.SerializerMethodField()
    article_review_url = serializers.SerializerMethodField()

    def get_keywords_list(self, obj):
        if obj.keywords:
            kw_list = obj.keywords.split(",")
            return kw_list 
        
        return None
    
    def get_article_review_url(self, obj):
        request = self.context.get('request')
        if not request:       
            logger.warning("No request provided in the serializer context")

        review = None 
        if request and request.user.client:            
            # Fetch the first article review for the article and client
            review = ArticleReview.objects.filter(article=obj, search__literature_review__client__in=request.user.my_companies).first()
            
        elif request:
            review = ArticleReview.objects.filter(article=obj).first()
        
        # Return the absolute URL if the review exists
        if review:
            return review.get_absolute_url()
        
        return None  # If no review exists, return None
        
    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "abstract",
            "citation",
            "full_text",
            "url",
            "keywords_list",
            "pubmed_uid",
            "pmc_uid",
            "doi",
            "article_review_url", 
            "is_added_to_library",
            "highlighted_full_text",
        ]

class NCBIDatabaseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = NCBIDatabase 
        fields = "__all__"

class ArticleTagSerializer(serializers.ModelSerializer):
    hex_to_rgba = serializers.SerializerMethodField()

    def get_hex_to_rgba(self, obj):
        return obj.hex_to_rgba() 
     
    class Meta:
        model = ArticleTag 
        fields = [
            "id",
            "literature_review",
            "creator",
            "name",
            "description",
            "color",
            "hex_to_rgba"
        ]

class PotentialDuplicateForSerializer(serializers.ModelSerializer):
    state = serializers.CharField(source="get_state_display")
    article = ArticleSerializer()
    absolute_url = serializers.SerializerMethodField()

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()

    class Meta:
        model = ArticleReview
        fields = ["id", "state", "article", "absolute_url"]


class ArticleReviewHistoricalStatusRequestSerializer(serializers.Serializer):
    article = serializers.PrimaryKeyRelatedField(queryset=ArticleReview.objects.all())
    
    def __init__(self, instance=None, data=..., **kwargs):
        super().__init__(instance, data, **kwargs)

        lit_review = self.context.get('literature_review')
        # or any custom logic
        self.fields['article'].queryset = ArticleReview.objects.filter(search__literature_review=lit_review)

    def create(self, validated_data):
        return validated_data["article"]


class ArticleReviewHistoricalStatusResponseSerializer(serializers.ModelSerializer):
    previous_article_state = serializers.SerializerMethodField()


    def get_previous_article_state(self, obj):
        if obj.article_history.count() > 0:
            article_history = obj.article_history
            request = self.context.get("request")
            if request and request.user.client:
                article_history = article_history.filter(search__literature_review__in=request.user.my_reviews())

            for article_rev in article_history:
                if article_rev.state == "I" or article_rev.state == "E":
                    return  article_rev.get_state_display() + " - " + str(article_rev.search.literature_review) 
        
        return None


    class Meta:
        model = ArticleReview
        fields = [
            "id",
            "previous_article_state",
        ]

class ArticleReviewSerializer(serializers.ModelSerializer):
    is_sota_term = serializers.BooleanField(source="search.is_sota_term")
    article = ArticleSerializer()
    state = serializers.CharField(source="get_state_display")
    state_symbole = serializers.CharField(source="state")
    absolute_url = serializers.SerializerMethodField()
    database = NCBIDatabaseSerializer(source="search.db")
    tags = ArticleTagSerializer(many=True)
    search_term = serializers.SerializerMethodField()
    client = serializers.SerializerMethodField()
    literature_review = serializers.SerializerMethodField()
    clinical_app_link = serializers.SerializerMethodField()
    potential_duplicate_for = PotentialDuplicateForSerializer()

    def get_search_term(self, obj):
        return obj.search.term

    def get_client(self, obj):
        return str(obj.search.literature_review.client)

    def get_literature_review(self, obj):
        return str(obj.search.literature_review)

    def get_absolute_url(self, obj):
        return obj.get_absolute_url()

    def get_clinical_app_link(self, obj):
        clin_appr = obj.clin_lit_appr.first()
        if clin_appr:
            return reverse(
                "lit_reviews:clinical_literature_appraisal", 
                kwargs={"id": obj.search.literature_review.id, "appraisal_id": clin_appr.id}
            )
        else:
            return None
    
    class Meta:
        model = ArticleReview
        fields = [
            "id",
            "state",
            "state_symbole",
            "exclusion_reason",
            "exclusion_comment",
            "score",
            "is_sota_term",
            "processed_abstract",
            "processed_title",
            "article",
            "absolute_url",
            "database",
            "notes",
            "tags",
            "search_term",
            "literature_review",
            "client",
            "clinical_app_link",
            "potential_duplicate_for",
            "ai_state_decision",
            "ai_exclusion_reason",
            "ai_decision_accepted",
        ]


class ExclusionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExclusionReason
        fields = "__all__"

class ArticleReviewUpdateSerializer(serializers.ModelSerializer):
    tags_ids = serializers.ListField(write_only=True)
    class Meta:
        model = ArticleReview
        fields = [
            "state",
            "exclusion_reason",
            "tags_ids",
            "notes",
            "exclusion_comment",
        ]

    def update(self, instance, validated_data):
        from lit_reviews.tasks import check_full_article_link_async

        tags_ids = validated_data.pop('tags_ids', None)
        super().update(instance, validated_data)

        if tags_ids != None and len(tags_ids) == 0:
            instance.tags.clear()

        if tags_ids:
            instance.tags.clear()
            for tag_id in tags_ids:
                tag = ArticleTag.objects.get(id=tag_id)
                if tag not in instance.tags.all():
                    instance.tags.add(tag)

        ### Get Article Full Text if available ####
        request = self.context.get("request")
        user_id = None 
        if request:
            user_id = request.user.id
        if instance and not instance.article.full_text:
            check_full_article_link_async.delay(instance.article.id, instance.id, user_id)

        return instance
    


class DuplicatesGroupSerializer(serializers.ModelSerializer):
    original_article_review = ArticleReviewSerializer()
    duplicates = ArticleReviewSerializer(many=True)
    duplication_count = serializers.SerializerMethodField()

    def get_duplication_count(self, obj):
        # Count duplicates
        return obj.duplicates.count()
    
    class Meta:
        model = DuplicatesGroup
        fields = [
            "original_article_review",
            "duplicates",
            "duplication_count",
        ]


class FullTextUploaderArticleReviewSerializer(serializers.ModelSerializer):
    article = ArticleSerializer()
    database = serializers.SerializerMethodField()
    full_text_file_name = serializers.SerializerMethodField()

    class Meta:
        model = ArticleReview
        fields = [
            "id",
            "article",
            "database",
            "full_text_status",
            "full_text_file_name",
        ]

    def get_database(self, obj):
        if obj.search.db.displayed_name:
            return obj.search.db.displayed_name
        else:
            return obj.search.db.name
    
    def get_full_text_file_name(self, obj):
        if obj.article.full_text:
            file_name = obj.article.full_text.name
            file_name = file_name.split("/")[-1]
            return file_name
        return None 
    
class UploadFullTextSerializer(serializers.Serializer):
    article_review = serializers.PrimaryKeyRelatedField(queryset=ArticleReview.objects.all(), required=True)
    aws_file_key = serializers.CharField(required=True)

    def validate(self, data):
        super().validate(data)
        article_review = data.get("article_review")
        literature_review = self.context.get("literature_review")
        if article_review.search.literature_review != literature_review:
            raise serializers.ValidationError("You don't have permission to access this article review.")
        
        return data 
    
    def create(self, validated_data):
        request = self.context.get("request")
        article_review = validated_data.get("article_review")
        aws_file_key = validated_data.get("aws_file_key")

        article = article_review.article
        article.full_text.name = aws_file_key
        article.save()
        article_review.full_text_status = article_review.calculate_full_text_status()
        article_review.save()

        appraisal = ClinicalLiteratureAppraisal.objects.filter(article_review=article_review).first()
        if appraisal:
            appraisal.app_status = appraisal.status
            logger.info("Full text file uploaded successfully")
            logger.info("clinical_literature_appraisal_id: {0}".format(appraisal.id))
            
            customer_settings = get_customer_settings(request.user)            
            if customer_settings and customer_settings.automatic_ai_extraction:
                logger.info("Automatic AI extraction is enabled - processing appraisal asynchronously")
                appraisal_ai_extraction_generation_async.delay(appraisal.id, request.user.id)
            else:
                logger.info("Automatic AI extraction is disabled - skipping AI processing")

        return article_review
    

class ClearFullTextSerializer(serializers.Serializer):
    article_review = serializers.PrimaryKeyRelatedField(queryset=ArticleReview.objects.all(), required=True)

    def validate(self, data):
        super().validate(data)
        article_review = data.get("article_review")
        literature_review = self.context.get("literature_review")
        if article_review.search.literature_review != literature_review:
            raise serializers.ValidationError("You don't have permission to access this article review.")
        
        return data 
    
    def create(self, validated_data):
        article_review = validated_data.get("article_review")
        article_review.article.full_text = ""
        article_review.article.save()

        article_review.full_text_status = article_review.calculate_full_text_status()
        article_review.save()
        
        return article_review