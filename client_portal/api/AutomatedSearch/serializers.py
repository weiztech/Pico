from django.urls import reverse
from rest_framework import serializers

from client_portal.models import (
    AutomatedSearchProject,
    ArticleComment,
    LibraryEntry,
)
from lit_reviews.models import (
    Device,
    Manufacturer,
    NCBIDatabase,
    Article,
    LiteratureSearch,
    ArticleReview,
    Client,
)


class AutomatedSearchProjectSerializer(serializers.ModelSerializer):
    device = serializers.SerializerMethodField()
    search_status = serializers.SerializerMethodField()

    class Meta:
        model  = AutomatedSearchProject
        fields = "__all__"

    def get_device(self, obj):
        device = obj.lit_review.device
        device_serializer = DeviceSerializer(device)
        return device_serializer.data
    
    def get_search_status(self, obj):
        searches = LiteratureSearch.objects.filter(literature_review=obj.lit_review)
        failed = any([( search.import_status == "INCOMPLETE-ERROR" and obj.terms == search.term) for search in searches])
        is_pending = any([( search.import_status != "COMPLETE" and obj.terms == search.term)for search in searches]) 
        if failed:
            return "Failed"
        elif is_pending:
            return "Pending"
        else:
            return "Completed" 


class DeviceSerializer(serializers.ModelSerializer):
    device_name = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ["id", "device_name"]

    def get_device_name(self, obj):
        return obj.__str__()
    

class ManufacturerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Manufacturer
        fields = ["name"]


class NCBIDatabaseSerializer(serializers.ModelSerializer):

    class Meta:
        model = NCBIDatabase
        fields = "__all__"

class ClientSerailizer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = "__all__"

class ArticleCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.SerializerMethodField()
    class Meta:
        model = ArticleComment
        fields = "__all__"

    def get_user_username(self, obj):
        return obj.user.username


class ArticleSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    class Meta:
        model = Article
        fields = "__all__"
    
    def get_comments(self, obj):
        comments_data = ArticleComment.objects.filter(article=obj).order_by("-date_time")
        comments_serializer = ArticleCommentSerializer(comments_data, many=True)
        return comments_serializer.data
    
    def get_is_saved(self, obj):
        library_entry = LibraryEntry.objects.filter(article = obj)
        if library_entry:
            return True
        else:
            return False
        

class ArticleReviewSerializer(serializers.ModelSerializer):
    article = ArticleSerializer()
    database = serializers.SerializerMethodField()
    term = serializers.SerializerMethodField()

    class Meta:
        model = ArticleReview
        fields = "__all__"

    def get_database(self, obj):
        return obj.search.db.displayed_name

    def get_term(self, obj):
        return obj.search.term

class DateRangesFilterValuesSerailizer(serializers.Serializer):
    id = serializers.CharField()
    value = serializers.CharField()