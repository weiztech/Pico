from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import serializers
import datetime

from backend.logger import logger
from lit_reviews.models import (
    LiteratureReview,
    LiteratureSearch,
    LiteratureReviewSearchProposal,
    NCBIDatabase,
    ArticleReview,
    Article,
    ArticleTag
)


class NCBIDatabaseSerializer(ModelSerializer):

    class Meta:
        model = NCBIDatabase
        fields = '__all__'


class CreateNewSearchNotebookTermSerializer(serializers.Serializer):
    term = serializers.CharField()
    start_search_interval = serializers.DateField()
    end_search_interval = serializers.DateField()
    db = serializers.CharField()

    def create(self, validated_data):
        # from lit_reviews.helpers.search_terms import update_search_terms
        from lit_reviews.tasks import run_auto_search

        user_id = self.context.get("user_id")
        lit_review_id = self.context.get("lit_review_id")
        lit_review = LiteratureReview.objects.get(id=lit_review_id)

        db = NCBIDatabase.objects.get(entrez_enum=validated_data.get("db"))
        
        # new_prop = LiteratureReviewSearchProposal.objects.create(
        #     literature_review = lit_review,
        #     term = validated_data.get("term"),
        #     db = db,
        #     result_count = -1,
        # )
        new_search = LiteratureSearch.objects.create(
            literature_review = lit_review,
            db = db,
            result_count = -1,
            term = validated_data.get("term"),
            start_search_interval = validated_data.get("start_search_interval"),
            end_search_interval = validated_data.get("end_search_interval"),
            is_notebook_search = True,
            import_status="RUNNING",
        )
        # new_prop.literature_search = new_search
        # new_prop.save()

        # Serialize the new_search object
        serialized_search = LiteratureSearchSerializer(new_search)

        # run_auto_search_task
        run_auto_search.delay(lit_review_id, new_search.id, user_id)

        return serialized_search.data
    
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"

class ArticleTagSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ArticleTag 
        fields = [
            "id",
            "literature_review",
            "creator",
            "name",
            "description",
            "color",
        ]

class ArticleReviewSerializer(serializers.ModelSerializer):
    database = serializers.SerializerMethodField()
    article = ArticleSerializer()
    tags = ArticleTagSerializer(many=True)
    class Meta:
        model = ArticleReview
        fields = "__all__"

    def get_database(self, obj):
        if obj.search and obj.search.db:
            return NCBIDatabaseSerializer(obj.search.db).data
        return None


class LiteratureSearchSerializer(serializers.ModelSerializer):
    article_reviews = serializers.SerializerMethodField()
    db = NCBIDatabaseSerializer()
    limit_excluded = serializers.BooleanField()
    
    class Meta:
        model = LiteratureSearch
        fields = "__all__"

    def get_article_reviews(self, obj):
        # Query the related ArticleReview objects
        # reviews = ArticleReview.objects.filter(search=obj)
        # return ArticleReviewSerializer(reviews, many=True).data
        return ArticleReview.objects.filter(search=obj).count()

class LiteratureSearchUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = LiteratureSearch
        fields = ["id", "is_archived"]


class UpdateArticleSerializer(serializers.ModelSerializer):
    article_review_id = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Article
        fields = ["id", "article_review_id", "is_added_to_library"]
