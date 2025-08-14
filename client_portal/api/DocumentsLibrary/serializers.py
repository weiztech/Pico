from django.urls import reverse
from rest_framework import serializers

from client_portal.models import Project
from lit_reviews.models import (
    Article,
    ArticleReview,
    NCBIDatabase,
    LiteratureReview,
    Device,
)
from lit_reviews.api.tags.serializers import ArticleTagSerializer

class DeviceSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ["id", "device_name"]

    def get_device_name(self, obj):
        return obj.__str__()

class ProjectSerializer(serializers.ModelSerializer):
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["id", "project_name", "lit_review"]

    def get_project_name(self, obj):
        return obj.project_name + " " + obj.lit_review.device.__str__()


class LiteratureReviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = LiteratureReview
        fields = ["id", "name"]

    def get_name(self, obj):
        return obj.__str__()

class NCBIDatabaseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = NCBIDatabase 
        fields = ["name", "displayed_name", "entrez_enum"]

class ReviewSerializer(serializers.Serializer):
    """
    Review Serializer combines LiteratureReview data + Article Review data.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    article_review_id = serializers.IntegerField()
    article_review_state = serializers.CharField()
    article_review_detail_link = serializers.CharField()


class ArticleSerializer(serializers.ModelSerializer):
    tags = ArticleTagSerializer(many=True)
    project = serializers.SerializerMethodField()

    class Meta:
        model  = Article
        fields = [
            "id",
            "tags",
            "title",
            "abstract",
            "citation",
            "pubmed_uid",
            "pmc_uid",
            "full_text",
            "publication_year",
            "literature_review",
            "project",
        ]

    def get_project(self, obj):
        project = Project.objects.filter(lit_review=obj.literature_review).first()
        if project:
            return project.id 

class CitationSerializer(serializers.Serializer):
    literature_reviews = serializers.SerializerMethodField()
    article = serializers.SerializerMethodField() 
    database = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"

    def get_article(self, object):
        return ArticleSerializer(object).data
    
    def get_database(self, object):
        
        if object.meta_data:
            db_name = object.meta_data.get("db")
            if db_name:
                db = NCBIDatabase.objects.filter(name=db_name).first()
                serailizer = NCBIDatabaseSerializer(db)
                return serailizer.data

        user = self.context.get("request").user
        # if user.client:
        #     article_reviews = ArticleReview.objects.filter(article=object, search__literature_review__client=user.client).distinct("search__literature_review")
        # elif user.is_ops_member:
        #     article_reviews = ArticleReview.objects.filter(article=object, search__literature_review__client__is_company=False).distinct("search__literature_review")
        # else:
        #     article_reviews = ArticleReview.objects.filter(article=object).distinct("search__literature_review")
            
        article_reviews = ArticleReview.objects.filter(article=object, search__literature_review__in=user.my_reviews()).distinct("search__literature_review")
        if article_reviews:
            article_review = article_reviews[0]
            serailizer = NCBIDatabaseSerializer(article_review.search.db)
            return serailizer.data
        else :
            return None
    
    def get_literature_reviews(self, object):
        lit_reviews = []
        lit_reviews_ids = []
        user = self.context.get("request").user
        article_reviews = ArticleReview.objects.filter(article=object, search__literature_review__in=user.my_reviews()).distinct("search__literature_review")
        
        if article_reviews.exists():
            for article_review in article_reviews:
                lit_review = article_review.search.literature_review
                article_review_link = reverse("lit_reviews:article_review_detail", kwargs={"id": lit_review.id, "article_id": article_review.id})
                notebook_view_link = reverse("lit_reviews:search_notebook")

                ser_values = {
                    "id":lit_review.id,
                    "name":lit_review.__str__(),
                    "article_review_id": article_review.id,
                    "article_review_state": article_review.state,
                    "article_review_detail_link": notebook_view_link if lit_review.is_notebook else article_review_link,
                }
                review_serializer = ReviewSerializer(ser_values)
                lit_reviews.append(review_serializer.data)
                lit_reviews_ids.append(lit_review.id)

        if object.literature_review and object.literature_review.id not in lit_reviews_ids:
            ser_values = {
                "id":object.literature_review.id,
                "name":object.literature_review.__str__(),
                "article_review_id": None,
                "article_review_state": "",
                "article_review_detail_link": reverse("lit_reviews:literature_review_detail", kwargs={"id": object.literature_review.id}),
            }
            review_serializer = ReviewSerializer(ser_values)
            lit_reviews.append(review_serializer.data)
            lit_reviews_ids.append(object.literature_review.id)

        return lit_reviews


class UpdateArticleSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), required=False)

    class Meta:
        model = Article 
        fields = [
            "id",
            "title",
            "citation",
            "abstract",
            "publication_year",
            "full_text",
            "pubmed_uid",
            "pmc_uid",
            "project",
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'pubmed_uid': {'read_only': True},
            'pmc_uid': {'read_only': True},
        }
    
    def update(self, instance, validated_data):
        project = validated_data.pop("project")
        article = super().update(instance, validated_data)

        if project:
            article.literature_review = project.lit_review
            article.save()

        return article